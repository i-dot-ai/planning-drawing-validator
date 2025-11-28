import logging
from pathlib import Path
from typing import Any

from planning_drawing_validator.llm import LLMProtocol, get_llm_client
from planning_drawing_validator.models import CarbonImpact
from planning_drawing_validator.pipeline.schemas import ClassificationResponse

logger = logging.getLogger(__name__)


class StageRunner:
    """Unified runner for all pipeline stages with consistent interface.

    All stages follow the same execution pattern:
    1. Load prompt from prompts/{stage}.txt
    2. Get Pydantic schema model(s)
    3. Call LLM with structured output
    4. Post-process result if needed
    """

    def __init__(
        self,
        prompts_dir: str | Path | None = None,
        llm: LLMProtocol | None = None,
        run_id: str | None = None,
        reasoning_effort: str | None = None,
        convert_pdf_to_images: bool = False,
    ) -> None:
        """Initialise stage runner.

        Args:
            prompts_dir: Optional prompts directory override
            llm: Optional LLM client instance conforming to LLMProtocol. If not provided, uses singleton.
            run_id: Optional run ID for tracing/grouping LLM calls
            reasoning_effort: Optional reasoning/thinking effort level for LLM calls.
                Values: "none" (disabled), "low", "medium", "high".
                If None, uses provider defaults.
            convert_pdf_to_images: Whether to convert PDFs to images before sending to LLM.
                Required for Azure-hosted OpenAI models which don't support 'file' content type.
        """
        from planning_drawing_validator.config import PathConfig

        self.prompts_dir = Path(prompts_dir) if prompts_dir else PathConfig.default().prompts_dir
        # Use provided LLM or get singleton for efficient resource management
        self.llm = llm or get_llm_client()
        self.run_id = run_id
        self.reasoning_effort = reasoning_effort
        self.convert_pdf_to_images = convert_pdf_to_images

    def _load_prompt(self, stage_name: str) -> str:
        """Load prompt text from file.

        Args:
            stage_name: Stage name (classification or validation_*)

        Returns:
            Prompt text

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_file = self.prompts_dir / f"{stage_name}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"{stage_name.title()} prompt not found: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8")

    async def run_classification(
        self, image_data: Any, filename_hint: str | None = None
    ) -> tuple[ClassificationResponse, CarbonImpact | None, str | None]:
        """Run classification stage: identify document type.

        Args:
            image_data: Image to classify
            filename_hint: Optional filename for context

        Returns:
            Tuple of (ClassificationResponse, carbon impact, thinking content)
        """

        # 1. Load prompt from file
        prompt_text = self._load_prompt("classification")

        # 2. Add filename context if provided
        if filename_hint:
            prompt_text = f"{prompt_text}\n\n**Filename context:** The document filename is '{filename_hint}'. Use this as a hint but prioritise visual analysis of the actual document content."

        # 3. Call LLM with Pydantic model for structured output
        result, carbon_impact, thinking = await self.llm.generate_structured_output(
            [prompt_text, image_data],
            ClassificationResponse,
            trace_name=self.run_id,
            reasoning_effort=self.reasoning_effort,
            convert_pdf_to_images=self.convert_pdf_to_images,
        )

        # 5. Parse and validate into Pydantic model instance
        if not result:
            raise ValueError(
                "Classification failed: LLM returned empty response. "
                "This may be due to API timeout, network issues, or service unavailability. "
                "Please try again or check API connectivity."
            )

        # Log thinking content if available
        if thinking:
            logger.debug(f"Classification thinking available ({len(thinking)} chars)")

        return ClassificationResponse.model_validate(result), carbon_impact, thinking

    async def run_validation(
        self,
        image_data: Any,
        prompt_type: str,
        filename: str | None = None,
        location_context: str | None = None,
        constituent_drawings: list[dict[str, Any]] | None = None,
    ) -> tuple[Any, CarbonImpact | None, str | None]:
        """Run validation stage: validate against requirements.

        For mixed_plans, validates each constituent drawing separately and aggregates results.

        Args:
            image_data: Image to validate
            prompt_type: Document type for schema selection
            filename: Optional filename for context
            location_context: Optional location context (e.g., "top left panel", "bottom half")
            constituent_drawings: For mixed_plans, list of constituent drawing objects

        Returns:
            Tuple of (validation result, carbon impact, thinking content).
            ValidationResponse for single drawings, or dict with composite results for mixed_plans.
        """
        from planning_drawing_validator.pipeline.schemas import (
            VALIDATION_CHECK_MODELS,
            GenericValidationChecks,
            create_validation_response_model,
        )

        # Handle composite validation for mixed_plans
        if prompt_type == "mixed_plans" and constituent_drawings:
            result, carbon_impact, thinking = await self._validate_mixed_plans(
                image_data, constituent_drawings
            )
            return result, carbon_impact, thinking

        # Standard validation
        prompt_text = self._load_prompt("validation")

        # Add location context if provided
        if location_context:
            prompt_text = f"""{prompt_text}

**Focus Area:** On this document, focus validation on: {location_context}
"""

        validation_check_model = VALIDATION_CHECK_MODELS.get(prompt_type, GenericValidationChecks)
        validation_response_model = create_validation_response_model(validation_check_model)

        result, carbon_impact, thinking = await self.llm.generate_structured_output(
            [prompt_text, image_data],
            validation_response_model,
            trace_name=self.run_id,
            reasoning_effort=self.reasoning_effort,
            convert_pdf_to_images=self.convert_pdf_to_images,
        )

        # Log thinking content if available
        if thinking:
            logger.debug(f"Validation thinking available ({len(thinking)} chars)")

        return validation_response_model.model_validate(result), carbon_impact, thinking

    async def _validate_mixed_plans(
        self, image_data: Any, constituent_drawings: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], CarbonImpact | None, str | None]:
        """Validate each constituent drawing concurrently for better performance.

        Runs all constituent validations in parallel using asyncio.gather(),
        providing 3-5x performance improvement over sequential validation.

        Args:
            image_data: Image containing multiple drawings
            constituent_drawings: List of constituent drawing objects from classification

        Returns:
            Tuple of (dict with composite validation results, aggregated carbon impact, thinking content)
        """
        import asyncio

        from planning_drawing_validator.models import CarbonImpact

        async def validate_constituent(
            constituent: dict[str, Any],
        ) -> tuple[dict[str, Any], CarbonImpact | None, str | None]:
            """Validate a single constituent drawing.

            Args:
                constituent: Single constituent drawing object

            Returns:
                Tuple of (dict with drawing details and validation result, carbon impact)
            """
            # Extract constituent details
            drawing_type: str = (
                constituent.get("drawing_type", "unknown")
                if isinstance(constituent, dict)
                else constituent.drawing_type or "unknown"
            )
            description: str = (
                constituent.get("description", "")
                if isinstance(constituent, dict)
                else constituent.description or ""
            )
            location: str = (
                constituent.get("location_on_sheet", "")
                if isinstance(constituent, dict)
                else constituent.location_on_sheet or ""
            )

            # Build location context
            location_context = f"{drawing_type.replace('_', ' ')} at {location} ({description})"

            # Call run_validation for this constituent - now returns (result, carbon_impact, thinking)
            validated, carbon_impact, thinking = await self.run_validation(
                image_data=image_data,
                prompt_type=drawing_type,
                location_context=location_context,
            )

            return (
                {
                    "drawing_type": drawing_type,
                    "description": description,
                    "location": location,
                    "validation": validated.model_dump(),
                },
                carbon_impact,
                thinking,
            )

        # Run all validations concurrently
        constituent_results = await asyncio.gather(
            *[validate_constituent(c) for c in constituent_drawings],
            return_exceptions=True,
        )

        # Filter out exceptions and collect valid results + accumulate carbon
        valid_results: list[dict[str, Any]] = []
        carbon_impacts: list[CarbonImpact] = []
        thinking_contents: list[str] = []

        for i, result in enumerate(constituent_results):
            if isinstance(result, Exception):
                # Log error but continue with other constituents
                logger.error(f"Constituent {i} validation failed: {result}")
                continue
            # Type narrowing: result is tuple here (not an Exception)
            assert isinstance(result, tuple)
            validation_dict, carbon_impact, thinking = result
            valid_results.append(validation_dict)
            if carbon_impact:
                carbon_impacts.append(carbon_impact)
            if thinking:
                thinking_contents.append(
                    f"**{validation_dict['drawing_type'].replace('_', ' ').title()}:**\n{thinking}"
                )

        # Aggregate carbon impacts by summing all values
        total_carbon_impact = None
        if carbon_impacts:
            total_carbon_impact = CarbonImpact(
                energy_kwh_min=sum(c.energy_kwh_min for c in carbon_impacts),
                energy_kwh_max=sum(c.energy_kwh_max for c in carbon_impacts),
                gwp_kgco2eq_min=sum(c.gwp_kgco2eq_min for c in carbon_impacts),
                gwp_kgco2eq_max=sum(c.gwp_kgco2eq_max for c in carbon_impacts),
                adpe_kgsbeq_min=sum(c.adpe_kgsbeq_min for c in carbon_impacts),
                adpe_kgsbeq_max=sum(c.adpe_kgsbeq_max for c in carbon_impacts),
                pe_mj_min=sum(c.pe_mj_min for c in carbon_impacts),
                pe_mj_max=sum(c.pe_mj_max for c in carbon_impacts),
                wcf_l_min=sum(c.wcf_l_min for c in carbon_impacts),
                wcf_l_max=sum(c.wcf_l_max for c in carbon_impacts),
            )

        # Aggregate results
        all_valid = all(r["validation"]["validity_assessment"] != "INVALID" for r in valid_results)
        invalid_count = sum(
            1 for r in valid_results if r["validation"]["validity_assessment"] == "INVALID"
        )
        confidences = [r["validation"]["overall_confidence"] for r in valid_results]

        # Build composite reasoning from all constituent drawings
        reasoning_parts = []
        for r in valid_results:
            drawing_type = r["drawing_type"].replace("_", " ").title()
            location = r.get("location", "unknown location")
            validity = r["validation"]["validity_assessment"]
            drawing_reasoning = r["validation"].get("assessment_reasoning", "No reasoning provided")
            reasoning_parts.append(
                f"[{drawing_type} at {location}] {validity}: {drawing_reasoning}"
            )

        summary = f"Mixed plan with {len(valid_results)} drawings."
        if invalid_count > 0:
            summary += f" {invalid_count} failed validation."
        else:
            summary += " All drawings valid."

        composite_reasoning = f"{summary}\n\n" + "\n\n".join(reasoning_parts)

        result_dict = {
            "document_type": "mixed_plans",
            "validity_assessment": "VALID" if all_valid else "INVALID",
            "overall_confidence": "LOW"
            if "LOW" in confidences
            else ("MEDIUM" if "MEDIUM" in confidences else "HIGH"),
            "assessment_reasoning": composite_reasoning,
            "constituent_validations": valid_results,
        }

        # Combine all thinking content from constituent drawings
        combined_thinking = "\n\n".join(thinking_contents) if thinking_contents else None

        return result_dict, total_carbon_impact, combined_thinking
