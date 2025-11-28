import asyncio
import logging
from typing import Any

from planning_drawing_validator.models import Document
from planning_drawing_validator.validator import DocumentValidator

from backend.models import (
    ComparisonResult,
    EvaluationReport,
    GroundTruthDocument,
    create_evaluation_report,
)

logger = logging.getLogger(__name__)

__all__ = ["PerformanceEvaluator"]


class PerformanceEvaluator:
    """Evaluates document validator performance against test datasets.

    Uses DocumentValidator as a black box - calls it with test documents and
    compares predictions to expected results. This is purely for quality assurance
    and should NOT be deployed in production.

    The evaluator can run concurrent validations and provides detailed metrics
    including accuracy, precision, recall, and per-document comparisons.
    """

    def __init__(
        self,
        validator: DocumentValidator,
    ) -> None:
        """Initialise evaluator with production validator to test.

        Args:
            validator: Production DocumentValidator instance to evaluate.
        """
        self.validator = validator

    async def evaluate(
        self,
        test_dataset: list[GroundTruthDocument],
        max_concurrent: int = 5,
        progress_callback: Any = None,
    ) -> EvaluationReport:
        """Run evaluation against test dataset with concurrency control.

        Validates each test document using the production validator, then compares
        predictions to expected results to calculate performance metrics.

        Args:
            test_dataset: Documents with known expected validation results.
            max_concurrent: Maximum number of concurrent validations.
            progress_callback: Optional callback for progress updates.

        Returns:
            Evaluation report with accuracy metrics and per-document comparisons.
        """
        if not test_dataset:
            logger.warning("Empty test dataset provided")
            return EvaluationReport(
                total=0,
                correct=0,
                accuracy=0.0,
                results=[],
            )

        comparison_results: list[ComparisonResult] = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_and_compare(gt_doc: GroundTruthDocument) -> ComparisonResult:
            """Validate document and compare to expected result.

            Args:
                gt_doc: Ground truth document with expected result.

            Returns:
                Comparison of predicted vs expected.
            """
            async with semaphore:
                # Call production validator (black box)
                predicted = await self.validator.validate(gt_doc.document)

                # Compare prediction to expected (None if no ground truth)
                if gt_doc.expected_validity == "UNKNOWN":
                    correct = None
                else:
                    correct = predicted.validity == gt_doc.expected_validity

                # Notify progress callback if provided
                if progress_callback:
                    await progress_callback(gt_doc.document.document_id, predicted, correct)

                return ComparisonResult(
                    document_id=gt_doc.document.document_id,
                    predicted=predicted,
                    expected_validity=gt_doc.expected_validity,
                    correct=correct,
                    expected_reasoning=gt_doc.expected_reasoning,
                )

        # Run validations concurrently
        tasks = [validate_and_compare(gt_doc) for gt_doc in test_dataset]
        comparison_results = await asyncio.gather(*tasks)

        # Generate report with aggregate metrics
        return create_evaluation_report(comparison_results)

    async def evaluate_single(
        self,
        document: Document,
        expected_validity: str,
        expected_reasoning: str | None = None,
    ) -> ComparisonResult:
        """Evaluate a single document against expected result.

        Convenience method for validating and comparing a single document.

        Args:
            document: Document to validate.
            expected_validity: Expected validity assessment.
            expected_reasoning: Optional expected reasoning.

        Returns:
            Comparison result for the document.
        """
        # Validate using production validator
        predicted = await self.validator.validate(document)

        # Compare to expected (None if no ground truth)
        if expected_validity == "UNKNOWN":
            correct = None
        else:
            correct = predicted.validity == expected_validity

        return ComparisonResult(
            document_id=document.document_id,
            predicted=predicted,
            expected_validity=expected_validity,
            correct=correct,
            expected_reasoning=expected_reasoning,
        )
