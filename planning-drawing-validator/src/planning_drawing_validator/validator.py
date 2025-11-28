from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from planning_drawing_validator.config import get_config
from planning_drawing_validator.llm import LLMProtocol, get_llm_client
from planning_drawing_validator.models import (
    CarbonImpact,
    Document,
    IndividualDrawingResult,
    Requirement,
    ValidationResult,
)
from planning_drawing_validator.pipeline.runner import StageRunner
from planning_drawing_validator.storage import (
    LocalFileSystemStorage,
    ReadOnlyStorageProtocol,
)
from planning_drawing_validator.types import DocumentID, RunID, StoragePrefix

logger = logging.getLogger(__name__)

__all__ = ["DocumentValidator"]


class DocumentValidator:
    """Document validator - classify and validate planning documents.

    This is the core class for document validation. It takes a document,
    runs it through the classification and validation pipeline, and returns the result.
    """

    def __init__(
        self,
        max_concurrent: int | None = None,
        storage_prefix: StoragePrefix | None = None,
        stage_callback: Callable[[str, DocumentID, dict[str, Any]], Awaitable[None]] | None = None,
        run_id: RunID | None = None,
        llm_client: LLMProtocol | None = None,
        storage: ReadOnlyStorageProtocol | None = None,
        reasoning_effort: str | None = None,
        convert_pdf_to_images: bool = False,
    ) -> None:
        """Initialise validator with LLM client and optional storage.

        Args:
            max_concurrent: Optional concurrency override for LLM calls.
            storage_prefix: Optional prefix/scope for document storage (e.g., 'runs/123/' for S3,
                container prefix for Azure, etc.). Used with custom storage implementations.
            stage_callback: Optional async callback invoked after each stage completes.
                Signature: async def callback(stage_name: str, document_id: DocumentID, data: dict) -> None
            run_id: Optional run ID for tracing/grouping LLM calls in Langfuse.
            llm_client: Optional LLM client instance conforming to LLMProtocol (for testing/dependency injection).
            storage: Optional read-only storage implementation conforming to ReadOnlyStorageProtocol.
                If not provided, uses default LocalFileSystemStorage with data_dir.
                Applications can provide custom implementations (S3, Azure, GCS, etc.).
                Note: Validator only needs READ access - write/delete not required.
            reasoning_effort: Optional reasoning/thinking effort level for LLM calls.
                Values: "none" (disabled), "low", "medium", "high".
                If None, uses provider defaults.
            convert_pdf_to_images: Whether to convert PDFs to images before sending to LLM.
                Required for Azure-hosted OpenAI models which don't support 'file' content type.
        """
        self.model_config, self.path_config = get_config()
        self.path_config.ensure_directories()
        self.storage_prefix = storage_prefix
        self.stage_callback = stage_callback
        self.run_id = run_id
        self.reasoning_effort = reasoning_effort
        self.convert_pdf_to_images = convert_pdf_to_images

        if max_concurrent and max_concurrent > 0:
            self.model_config.max_concurrent = max_concurrent

        self.llm = llm_client or get_llm_client()
        self.stage_runner = StageRunner(
            llm=self.llm,
            run_id=run_id,
            reasoning_effort=reasoning_effort,
            convert_pdf_to_images=convert_pdf_to_images,
        )

        # Use provided storage or create default local filesystem storage
        self.storage = storage or LocalFileSystemStorage(base_dir=self.path_config.data_dir)

    async def validate(
        self, document: Document, humanise_reasoning: bool = False
    ) -> ValidationResult:
        """Validate a planning document through classification and validation pipeline.

        This is the main method. Takes a document, validates it, returns result.

        Args:
            document: Document to validate (with document_id, filename, optional storage_key).
            humanise_reasoning: If True, generate user-friendly reasoning summaries.

        Returns:
            Validation result with classification and validity assessment.
        """
        start_time = time.time()

        try:
            # Step 1: Resolve and encode document
            doc_source = self._resolve_document_source(document, start_time)
            if isinstance(doc_source, ValidationResult):  # Error result
                return doc_source

            # Convert storage identifier to bytes if needed
            document_part: Path | bytes
            if isinstance(doc_source, str):
                # It's a storage identifier, fetch the bytes
                doc_bytes = self.storage.get_document(doc_source)
                if doc_bytes is None:
                    return self._error(
                        document,
                        f"Failed to retrieve document from storage: {doc_source}",
                        start_time,
                    )
                document_part = doc_bytes
            elif isinstance(doc_source, Path):
                # It's a local file path, pass directly to LLM
                document_part = doc_source
            else:
                return self._error(
                    document,
                    f"Unexpected document source type: {type(doc_source)}",
                    start_time,
                )

            # Step 2: Classification stage
            (
                classification,
                classification_carbon,
                classification_thinking,
            ) = await self._run_classification(document, document_part)

            # Route to appropriate validation schema based on document type
            known_types = {
                "section_drawing",
                "floor_plan",
                "elevation",
                "location_plan",
                "site_plan",
                "roof_plan",
                "detail_drawing",
                "mixed_plans",
            }
            prompt_type = (
                classification.document_type
                if classification.document_type in known_types
                else "general"
            )

            # Step 3: Validation stage
            constituent_drawings = (
                [c.model_dump() for c in classification.constituent_drawings]
                if classification.constituent_drawings
                else None
            )
            (
                validation,
                validation_carbon,
                validation_thinking,
            ) = await self._run_validation(
                document, document_part, prompt_type, constituent_drawings
            )

            # Step 4: Accumulate carbon impacts from both stages
            total_carbon = self._accumulate_carbon_impacts(classification_carbon, validation_carbon)

            # Step 5: Process validation result
            (
                validity,
                reasoning,
                confidence,
                validation_checks,
                is_mixed,
                constituent_list,
            ) = self._process_validation_result(validation)

            # Step 6: Extract requirements from validation checks
            requirements = self._extract_requirements(validation_checks)

            # Step 7: Humanise reasoning if requested
            humanised = None
            humanised_constituent_list = constituent_list
            if humanise_reasoning and reasoning:
                humanised, humanised_constituent_list = await self._humanise_reasoning(
                    reasoning=reasoning,
                    validity=validity,
                    is_mixed=is_mixed,
                    constituent_drawings=constituent_list,
                )

            # Step 8: Build and return result
            return self._build_validation_result(
                document=document,
                doc_type=classification.document_type,
                prompt_type=prompt_type,
                validity=validity,
                reasoning=reasoning,
                confidence=confidence,
                requirements=requirements,
                is_mixed_drawing=is_mixed,
                constituent_drawings=humanised_constituent_list,
                classification=classification,
                carbon_impact=total_carbon,
                classification_thinking=classification_thinking,
                validation_thinking=validation_thinking,
                start_time=start_time,
                humanised_reasoning=humanised,
            )

        except Exception as e:
            logger.exception(f"Error validating {document.document_id}: {type(e).__name__}: {e}")
            return self._error(document, f"{type(e).__name__}: {e}", start_time)

    def _resolve_document_source(
        self, document: Document, start_time: float
    ) -> str | Path | ValidationResult:
        """Resolve document source using storage abstraction.

        Args:
            document: Document to resolve.
            start_time: Start time for error tracking.

        Returns:
            Document source (storage identifier or Path), or ValidationResult if error.
        """
        # If storage_key provided directly, use it
        if document.storage_key:
            logger.debug(f"Using storage_key from document: {document.storage_key}")
            return document.storage_key

        # If file_path provided directly, validate and use it
        if document.file_path:
            doc_path = Path(document.file_path)
            if not doc_path.exists() or not doc_path.is_file():
                return self._error(document, f"File not found: {document.file_path}", start_time)
            return doc_path

        # Search for document using storage abstraction
        search_prefix = self.storage_prefix or str(self.path_config.data_dir)
        logger.debug(f"Searching for {document.filename} in {search_prefix}")

        doc_identifier = self.storage.find_document(search_prefix, document.filename)
        if not doc_identifier:
            return self._error(document, f"Document not found: {document.filename}", start_time)

        return doc_identifier

    async def _run_classification(
        self, document: Document, document_part: Path | bytes
    ) -> tuple[Any, CarbonImpact | None, str | None]:
        """Run classification stage and notify callback.

        Args:
            document: Document being validated.
            document_part: Document to pass to LLM (Path or bytes).

        Returns:
            Tuple of (classification result, carbon impact, thinking content).
        """
        filename_hint = document.filename or document.document_id
        (
            classification,
            carbon_impact,
            thinking,
        ) = await self.stage_runner.run_classification(document_part, filename_hint)

        if self.stage_callback:
            await self.stage_callback(
                "classification",
                document.document_id,
                {
                    "document_type": classification.document_type,
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning,
                    "raw_response": classification,
                    "constituent_drawings": classification.constituent_drawings,
                },
            )

        return classification, carbon_impact, thinking

    async def _run_validation(
        self,
        document: Document,
        document_part: Path | bytes,
        prompt_type: str,
        constituent_drawings: list[dict[str, Any]] | None,
    ) -> tuple[Any, CarbonImpact | None, str | None]:
        """Run validation stage and notify callbacks.

        Args:
            document: Document being validated.
            document_part: Document to pass to LLM (Path or bytes).
            prompt_type: Type of validation prompt to use.
            constituent_drawings: Constituent drawing data for mixed plans.

        Returns:
            Tuple of (validation result, carbon impact, thinking content).
        """
        if self.stage_callback:
            await self.stage_callback("validation_started", document.document_id, {})

        validation, carbon_impact, thinking = await self.stage_runner.run_validation(
            document_part, prompt_type, constituent_drawings=constituent_drawings
        )

        # Build validation data for callback
        if isinstance(validation, dict):
            validation_data = {
                "validity_assessment": validation.get("validity_assessment", "UNKNOWN"),
                "reasoning": validation.get("assessment_reasoning", ""),
                "confidence": validation.get("overall_confidence", "LOW"),
                "raw_response": validation,
                "is_composite": True,
                "constituent_validations": validation.get("constituent_validations", []),
            }
        else:
            validation_data = {
                "validity_assessment": validation.validity_assessment or "UNKNOWN",
                "reasoning": validation.assessment_reasoning or "",
                "confidence": validation.overall_confidence or "LOW",
                "raw_response": validation,
                "is_composite": False,
            }

        if self.stage_callback:
            await self.stage_callback("validation", document.document_id, validation_data)

        return validation, carbon_impact, thinking

    def _process_validation_result(
        self, validation: Any
    ) -> tuple[str, str, str, Any, bool, list[IndividualDrawingResult] | None]:
        """Process validation result into standardised components.

        Args:
            validation: Raw validation result (dict for mixed plans, Pydantic model otherwise).

        Returns:
            Tuple of (validity, reasoning, confidence, validation_checks, is_mixed, constituent_list).
        """
        if isinstance(validation, dict):
            # Mixed plans composite result
            return self._process_mixed_plan_result(validation)

        # Standard single-drawing validation
        validity = validation.validity_assessment or "UNKNOWN"
        reasoning = validation.assessment_reasoning or ""
        confidence = validation.overall_confidence or "LOW"
        validation_checks = (
            validation.validation_checks.model_dump()
            if hasattr(validation, "validation_checks")
            else []
        )
        return validity, reasoning, confidence, validation_checks, False, None

    def _process_mixed_plan_result(
        self, validation: dict[str, Any]
    ) -> tuple[str, str, str, Any, bool, list[IndividualDrawingResult]]:
        """Process mixed plan validation result.

        Args:
            validation: Dict containing mixed plan validation data.

        Returns:
            Tuple of (validity, reasoning, confidence, validation_checks, is_mixed, constituent_list).
        """
        validity = validation.get("validity_assessment", "UNKNOWN")
        reasoning = validation.get("assessment_reasoning", "")
        confidence = validation.get("overall_confidence", "LOW")
        validation_checks = validation.get("validation_checks", [])

        constituent_drawings_list = []
        constituent_validations = validation.get("constituent_validations", [])

        for const_val in constituent_validations:
            validation_data = const_val.get("validation", {})
            validation_checks_dict = validation_data.get("validation_checks", {})

            # Convert validation checks to requirements
            const_reqs = [
                self._build_requirement_from_check(check_key, check_val)
                for check_key, check_val in validation_checks_dict.items()
                if isinstance(check_val, dict)
            ]

            constituent_drawings_list.append(
                IndividualDrawingResult(
                    drawing_type=const_val.get("drawing_type", "UNKNOWN"),
                    validity=validation_data.get("validity_assessment", "UNKNOWN"),
                    reasoning=validation_data.get("assessment_reasoning", ""),
                    confidence=validation_data.get("overall_confidence", "LOW"),
                    requirements_checked=const_reqs,
                )
            )

        return (
            validity,
            reasoning,
            confidence,
            validation_checks,
            True,
            constituent_drawings_list,
        )

    def _build_requirement_from_check(
        self, check_key: str, check_val: dict[str, Any]
    ) -> Requirement:
        """Build Requirement object from validation check.

        Args:
            check_key: Name of the check.
            check_val: Dict containing status, evidence, value.

        Returns:
            Requirement object.
        """
        llm_status = check_val.get("status", "UNKNOWN")
        req_status = self._map_validation_status(llm_status)

        evidence = check_val.get("evidence", "")
        value = check_val.get("value")
        details = f"{value}: {evidence}" if value and evidence else (value or evidence or None)

        return Requirement(
            requirement=check_key.replace("_", " ").title(),
            status=req_status,
            details=details,
        )

    def _extract_requirements(self, validation_checks: Any) -> list[Requirement]:
        """Extract requirements from validation checks.

        Args:
            validation_checks: Validation checks (dict, list, or other).

        Returns:
            List of Requirement objects.
        """
        if isinstance(validation_checks, dict):
            return [
                self._build_requirement_from_check(key, value)
                for key, value in validation_checks.items()
                if isinstance(value, dict)
            ]

        if isinstance(validation_checks, list):
            return [
                Requirement(
                    requirement=check.get("requirement", "Unknown"),
                    status=self._map_validation_status(check.get("status", "UNKNOWN")),
                    details=check.get("details"),
                )
                for check in validation_checks
                if isinstance(check, dict)
            ]

        return []

    def _accumulate_carbon_impacts(
        self,
        classification_carbon: CarbonImpact | None,
        validation_carbon: CarbonImpact | None,
    ) -> CarbonImpact | None:
        """Accumulate carbon impacts from classification and validation stages.

        Args:
            classification_carbon: Carbon impact from classification stage.
            validation_carbon: Carbon impact from validation stage.

        Returns:
            Combined CarbonImpact with summed values, or None if both are None.
        """
        if not classification_carbon and not validation_carbon:
            return None

        if not classification_carbon:
            return validation_carbon

        if not validation_carbon:
            return classification_carbon

        # Sum all impact metrics from both stages
        return CarbonImpact(
            energy_kwh_min=classification_carbon.energy_kwh_min + validation_carbon.energy_kwh_min,
            energy_kwh_max=classification_carbon.energy_kwh_max + validation_carbon.energy_kwh_max,
            gwp_kgco2eq_min=classification_carbon.gwp_kgco2eq_min
            + validation_carbon.gwp_kgco2eq_min,
            gwp_kgco2eq_max=classification_carbon.gwp_kgco2eq_max
            + validation_carbon.gwp_kgco2eq_max,
            adpe_kgsbeq_min=classification_carbon.adpe_kgsbeq_min
            + validation_carbon.adpe_kgsbeq_min,
            adpe_kgsbeq_max=classification_carbon.adpe_kgsbeq_max
            + validation_carbon.adpe_kgsbeq_max,
            pe_mj_min=classification_carbon.pe_mj_min + validation_carbon.pe_mj_min,
            pe_mj_max=classification_carbon.pe_mj_max + validation_carbon.pe_mj_max,
            wcf_l_min=classification_carbon.wcf_l_min + validation_carbon.wcf_l_min,
            wcf_l_max=classification_carbon.wcf_l_max + validation_carbon.wcf_l_max,
        )

    async def _humanise_reasoning(
        self,
        reasoning: str,
        validity: str,
        is_mixed: bool,
        constituent_drawings: list[IndividualDrawingResult] | None,
    ) -> tuple[str, list[IndividualDrawingResult] | None]:
        """Generate user-friendly reasoning summaries.

        Takes technical validation reasoning and produces clear, readable summaries
        suitable for non-technical users.

        Args:
            reasoning: Technical reasoning from validation.
            validity: Overall validity assessment.
            is_mixed: Whether this is a mixed drawing document.
            constituent_drawings: Individual drawing results for mixed plans.

        Returns:
            Tuple of (humanised overall reasoning, updated constituent drawings with humanised reasoning).
        """
        # Prompt for overall summary of mixed plans
        mixed_overall_prompt = """You are a planning validation assistant. Summarise this technical validation for a planning officer.

Technical input:
{reasoning}

Write a brief 1-2 sentence summary stating:
- How many drawings were checked
- The overall outcome (all passed, some failed, all failed)

Style: Professional, concise, factual. No technical jargon. No bullet points for the overall summary.

Example: "This document contains 3 drawings. 2 passed validation but the floor plan requires corrections."

Output ONLY the summary, nothing else."""

        # Prompt for individual constituent drawings in mixed plans
        constituent_prompt = """You are a planning validation assistant. Rewrite this technical validation into a clear summary for a planning officer.

Technical input:
{reasoning}

Follow this EXACT structure:

**Issues Found:**
• [First issue in plain English]
• [Second issue if applicable]

**Action Required:**
[One sentence stating what needs to be fixed, or "None - drawing meets requirements" if valid]

Style rules:
- Never use technical codes like "scale=PRESENT" or "COMPLIANT/MISSING"
- Use plain English (e.g., "scale bar is missing" not "scale check failed")
- Be specific about what's wrong
- Keep each bullet point to one line
- Professional but approachable tone

Output ONLY the structured summary, nothing else."""

        # Prompt for singular (non-mixed) plans
        singular_prompt = """You are a planning validation assistant. Rewrite this technical validation into a clear summary for a planning officer.

Technical input:
{reasoning}

Follow this EXACT structure:

**Summary:** [One sentence overall assessment]

**Checks Passed:**
• [List key requirements that were met, 2-4 items max]

**Issues Found:**
• [List any problems in plain English]
• [Or state "None - all requirements met" if valid]

**Action Required:**
[One sentence stating what needs fixing, or "None - ready for review" if valid]

Style rules:
- Never use technical codes like "scale=PRESENT" or "COMPLIANT/MISSING"
- Use plain English throughout
- Be specific and helpful
- Professional but approachable tone

Output ONLY the structured summary, nothing else."""

        try:
            # Choose appropriate prompt based on document type
            if is_mixed:
                overall_prompt = mixed_overall_prompt
            else:
                overall_prompt = singular_prompt

            # Humanise overall reasoning
            humanised_overall = await self.llm.generate_text(
                prompt=overall_prompt.format(reasoning=reasoning),
                run_id=self.run_id,
            )

            # Humanise constituent drawings if present
            updated_constituents = None
            if is_mixed and constituent_drawings:
                updated_constituents = []
                for drawing in constituent_drawings:
                    if drawing.reasoning:
                        humanised_drawing_reasoning = await self.llm.generate_text(
                            prompt=constituent_prompt.format(reasoning=drawing.reasoning),
                            run_id=self.run_id,
                        )
                        updated_constituents.append(
                            IndividualDrawingResult(
                                drawing_type=drawing.drawing_type,
                                validity=drawing.validity,
                                reasoning=drawing.reasoning,
                                confidence=drawing.confidence,
                                requirements_checked=drawing.requirements_checked,
                                humanised_reasoning=humanised_drawing_reasoning,
                            )
                        )
                    else:
                        updated_constituents.append(drawing)

            return humanised_overall, updated_constituents

        except Exception as e:
            logger.warning(f"Failed to humanise reasoning: {e}")
            # Return original reasoning if humanisation fails
            return reasoning, constituent_drawings

    def _build_validation_result(
        self,
        document: Document,
        doc_type: str,
        prompt_type: str,
        validity: str,
        reasoning: str,
        confidence: str,
        requirements: list[Requirement],
        is_mixed_drawing: bool,
        constituent_drawings: list[IndividualDrawingResult] | None,
        classification: Any,
        carbon_impact: CarbonImpact | None,
        classification_thinking: str | None,
        validation_thinking: str | None,
        start_time: float,
        humanised_reasoning: str | None = None,
    ) -> ValidationResult:
        """Build final ValidationResult.

        Args:
            document: Original document.
            doc_type: Classified document type.
            prompt_type: Validation prompt type used.
            validity: Validity assessment.
            reasoning: Validation reasoning.
            confidence: Confidence level.
            requirements: List of requirements checked.
            is_mixed_drawing: Whether this is a mixed drawing.
            constituent_drawings: Individual drawing results for mixed plans.
            classification: Classification result.
            carbon_impact: Accumulated carbon impact from all LLM calls.
            classification_thinking: Gemini thinking from classification stage.
            validation_thinking: Gemini thinking from validation stage.
            start_time: Validation start time.
            humanised_reasoning: User-friendly version of reasoning (optional).

        Returns:
            Complete ValidationResult.
        """
        return ValidationResult(
            document_id=document.document_id,
            document_type=doc_type,
            validity=validity,
            reasoning=reasoning,
            confidence=confidence,
            requirements_checked=requirements,
            execution_time=time.time() - start_time,
            success=True,
            error_message=None,
            prompt_type=prompt_type,
            is_mixed_drawing=is_mixed_drawing,
            constituent_drawings=constituent_drawings,
            classification_confidence=classification.confidence,
            classification_reasoning=classification.reasoning,
            classification_thinking=classification_thinking,
            validation_thinking=validation_thinking,
            carbon_impact=carbon_impact,
            humanised_reasoning=humanised_reasoning,
        )

    def _map_validation_status(self, llm_status: str) -> str:
        """Map LLM validation status to Requirement status.

        Args:
            llm_status: Status from LLM validation check (COMPLIANT, PRESENT, MISSING, etc.)

        Returns:
            Mapped status: PASS, FAIL, or NOT_APPLICABLE
        """
        status_map = {
            "COMPLIANT": "PASS",
            "PRESENT": "PASS",
            "MISSING": "FAIL",
            "UNCLEAR": "FAIL",
            "NOT_APPLICABLE": "NOT_APPLICABLE",
        }
        return status_map.get(llm_status, llm_status)

    def _error(self, document: Document, message: str, start_time: float) -> ValidationResult:
        """Create error validation result.

        Args:
            document: Document that failed validation.
            message: Error message.
            start_time: Validation start time.

        Returns:
            ValidationResult with error details.
        """
        return ValidationResult(
            document_id=document.document_id,
            document_type="UNKNOWN",
            validity="ERROR",
            reasoning="",
            confidence="UNKNOWN",
            requirements_checked=[],
            execution_time=time.time() - start_time,
            success=False,
            error_message=message,
            prompt_type="ERROR",
        )
