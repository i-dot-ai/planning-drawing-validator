import logging
import time
from collections.abc import Callable
from typing import Any

from planning_drawing_validator.llm.factory import get_llm_client
from planning_drawing_validator.models import Document
from planning_drawing_validator.validator import DocumentValidator

from backend.models import EvaluationResult, GroundTruthDocument
from backend.services.reasoning_judge import ReasoningJudge
from backend.storage.client import StorageClient

logger = logging.getLogger(__name__)

__all__ = ["Evaluator"]


class Evaluator:
    """Evaluator for the evaluation system API.

    Wraps the production DocumentValidator and provides the interface expected
    by the evaluation router. Handles document loading from S3 or local storage,
    conversion between model types, and stage callbacks for progress tracking.
    """

    def __init__(
        self,
        max_concurrent: int | None = None,
        storage_prefix: str | None = None,
        stage_callback: Callable[..., Any] | None = None,
        run_id: str | None = None,
        validator: DocumentValidator | None = None,
        storage_client: StorageClient | None = None,
        model_name: str | None = None,
        reasoning_effort: str | None = None,
        convert_pdf_to_images: bool = False,
        evaluate_reasoning: bool = True,
    ):
        """Initialise evaluator.

        Args:
            max_concurrent: Maximum concurrent evaluations (unused, kept for compatibility)
            storage_prefix: S3 prefix for document storage
            stage_callback: Optional callback for stage completion events
            run_id: Run identifier for tracking
            validator: Optional DocumentValidator instance (for testing)
            storage_client: Optional StorageClient instance (for testing)
            model_name: Optional LiteLLM model identifier to use for this evaluation
            reasoning_effort: Optional reasoning/thinking effort level for LLM calls.
                Values: "none" (disabled), "low", "medium", "high".
                If None, uses provider defaults.
            convert_pdf_to_images: Whether to convert PDFs to images before sending to LLM.
                Required for Azure-hosted OpenAI models which don't support 'file' content type.
            evaluate_reasoning: Whether to evaluate reasoning quality using LLM-as-judge.
                Requires an additional LLM call per document with ground truth reasoning.
        """
        self.storage_prefix = storage_prefix
        self.stage_callback = stage_callback
        self.run_id = run_id
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.convert_pdf_to_images = convert_pdf_to_images
        self.evaluate_reasoning = evaluate_reasoning
        # Create storage client for MinIO access
        self.storage = storage_client or StorageClient()
        # Create LLM client with model override if specified
        llm_client = get_llm_client(model_name) if model_name else None
        # Use provided dependencies or create new ones (dependency injection pattern)
        # Pass storage to validator so it reads from MinIO instead of local filesystem
        self.validator = validator or DocumentValidator(
            storage_prefix=storage_prefix,
            stage_callback=stage_callback,
            run_id=run_id,
            storage=self.storage,
            llm_client=llm_client,
            reasoning_effort=reasoning_effort,
            convert_pdf_to_images=convert_pdf_to_images,
        )
        # Create reasoning judge for evaluating reasoning quality
        self.reasoning_judge = ReasoningJudge(model_name=model_name) if evaluate_reasoning else None

    async def evaluate(self, ground_truth: GroundTruthDocument) -> EvaluationResult:
        """Evaluate a single document.

        Args:
            ground_truth: Ground truth document with expected result

        Returns:
            Evaluation result with prediction and comparison to ground truth
        """
        start_time = time.time()

        try:
            # Load document content
            document = await self._load_document(ground_truth)

            # Call production validator
            validation_result = await self.validator.validate(document)

            # Evaluate reasoning quality if enabled and ground truth has reasoning
            reasoning_evaluation = None
            print(
                f"🧠 REASONING CHECK: doc={ground_truth.document.document_id}, "
                f"judge={self.reasoning_judge is not None}, "
                f"expected_reasoning={repr(ground_truth.expected_reasoning)[:80] if ground_truth.expected_reasoning else 'None'}",
                flush=True,
            )
            if self.reasoning_judge and ground_truth.expected_reasoning:
                try:
                    logger.info(f"Running reasoning evaluation for {ground_truth.document.document_id}")
                    reasoning_evaluation = await self.reasoning_judge.evaluate(
                        expected_reasoning=ground_truth.expected_reasoning,
                        predicted_reasoning=validation_result.reasoning,
                        trace_name=self.run_id,
                    )
                    logger.info(
                        f"Reasoning evaluation result for {ground_truth.document.document_id}: "
                        f"score={reasoning_evaluation.match_score}, evaluated={reasoning_evaluation.evaluated}"
                    )
                except Exception as e:
                    logger.warning(f"Reasoning evaluation failed for {ground_truth.document.document_id}: {e}")

            # Convert to evaluation result
            result = self._create_evaluation_result(
                ground_truth=ground_truth,
                validation_result=validation_result,
                execution_time=time.time() - start_time,
                reasoning_evaluation=reasoning_evaluation,
            )

            return result

        except Exception as e:
            logger.error(f"Evaluation failed for {ground_truth.document.document_id}: {e}")
            # Return error result
            return EvaluationResult(
                document_id=ground_truth.document.document_id,
                prompt_type="unknown",
                ground_truth_validity=ground_truth.expected_validity,
                ground_truth_reason=ground_truth.expected_reasoning,
                predicted_validity="ERROR",
                predicted_reasoning=f"Evaluation failed: {str(e)}",
                confidence="LOW",
                correct=None,
                requirements_checked=[],
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e),
                document_type=None,
            )

    async def _load_document(self, ground_truth: GroundTruthDocument) -> Document:
        """Create Document object from GroundTruthDocument.

        The validator will load the content itself using the storage_key or filename.
        We just need to pass the document metadata.

        Args:
            ground_truth: Ground truth with document location info

        Returns:
            Document object for validation (metadata only)
        """
        # Return the document metadata - validator will load content itself
        return ground_truth.document

    def _create_evaluation_result(
        self,
        ground_truth: GroundTruthDocument,
        validation_result: Any,
        execution_time: float,
        reasoning_evaluation: Any | None = None,
    ) -> EvaluationResult:
        """Convert ValidationResult to EvaluationResult.

        Args:
            ground_truth: Ground truth with expected result
            validation_result: Result from production validator
            execution_time: Time taken for evaluation
            reasoning_evaluation: Optional reasoning evaluation result from LLM judge

        Returns:
            Evaluation result with comparison
        """
        # Map ValidationResult to EvaluationResult format
        predicted_validity = validation_result.validity

        # Determine if prediction is correct
        correct = None
        if ground_truth.expected_validity and ground_truth.expected_validity != "UNKNOWN":
            correct = predicted_validity == ground_truth.expected_validity

        # Convert requirements to dict format
        requirements_checked = []
        if validation_result.requirements_checked:
            requirements_checked = [
                {
                    "requirement": req.requirement,
                    "status": req.status,
                    "details": req.details,
                }
                for req in validation_result.requirements_checked
            ]

        # Extract reasoning evaluation results
        reasoning_match_score = None
        reasoning_evaluated = False
        reasoning_explanation = None
        if reasoning_evaluation:
            reasoning_match_score = reasoning_evaluation.match_score
            reasoning_evaluated = reasoning_evaluation.evaluated
            reasoning_explanation = reasoning_evaluation.explanation

        return EvaluationResult(
            document_id=ground_truth.document.document_id,
            prompt_type="validation",  # Could be extracted from validator if needed
            ground_truth_validity=ground_truth.expected_validity,
            ground_truth_reason=ground_truth.expected_reasoning,
            predicted_validity=predicted_validity,
            predicted_reasoning=validation_result.reasoning or "",
            confidence=validation_result.confidence or "MEDIUM",
            correct=correct,
            requirements_checked=requirements_checked,
            execution_time=execution_time,
            success=True,
            error_message=None,
            document_type=validation_result.document_type,
            carbon_impact=validation_result.carbon_impact,
            reasoning_match_score=reasoning_match_score,
            reasoning_evaluated=reasoning_evaluated,
            reasoning_explanation=reasoning_explanation,
        )
