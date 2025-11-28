"""Response transformers for converting validation results to API responses."""

from typing import Any

from planning_drawing_validator.models import ValidationResult

from backend.schemas import (
    CarbonImpact,
    IndividualDrawing,
    RequirementCheck,
    ValidationResponse,
)
from backend.utils import normalise_document_type


def transform_requirement(req: Any) -> RequirementCheck:
    """Transform a requirement result to API format.

    Args:
        req: Requirement object from validation result

    Returns:
        RequirementCheck API schema
    """
    return RequirementCheck(
        requirement=req.requirement,
        status=str(req.status).upper(),
        details=req.details,
    )


def transform_individual_drawing(drawing: Any) -> IndividualDrawing:
    """Transform a constituent drawing to API format.

    Args:
        drawing: IndividualDrawing from validation result

    Returns:
        IndividualDrawing API schema
    """
    # Prefer humanised reasoning for user-friendly display, fall back to raw reasoning
    reasoning = getattr(drawing, "humanised_reasoning", None) or drawing.reasoning

    return IndividualDrawing(
        drawing_type=normalise_document_type(drawing.drawing_type) or "OTHER_PLANS",
        validity=str(drawing.validity).upper(),
        confidence=str(drawing.confidence).upper(),
        reasoning=reasoning,
        requirements_checked=[
            transform_requirement(req) for req in drawing.requirements_checked if req.status != "NOT_APPLICABLE"
        ],
    )


def transform_carbon_impact(carbon_impact: Any) -> CarbonImpact | None:
    """Transform carbon impact data to API format.

    Args:
        carbon_impact: Carbon impact data from validation result

    Returns:
        CarbonImpact schema or None
    """
    if not carbon_impact:
        return None

    return CarbonImpact(
        energy_kwh_min=carbon_impact.energy_kwh_min,
        energy_kwh_max=carbon_impact.energy_kwh_max,
        gwp_kgco2eq_min=carbon_impact.gwp_kgco2eq_min,
        gwp_kgco2eq_max=carbon_impact.gwp_kgco2eq_max,
        adpe_kgsbeq_min=carbon_impact.adpe_kgsbeq_min,
        adpe_kgsbeq_max=carbon_impact.adpe_kgsbeq_max,
        pe_mj_min=carbon_impact.pe_mj_min,
        pe_mj_max=carbon_impact.pe_mj_max,
        wcf_l_min=carbon_impact.wcf_l_min,
        wcf_l_max=carbon_impact.wcf_l_max,
    )


def transform_validation_result(document_id: str, result: ValidationResult) -> ValidationResponse:
    """Transform validation result to API response format.

    Args:
        document_id: Unique document identifier
        result: Validation result from DocumentValidator

    Returns:
        ValidationResponse ready for API return
    """
    # Filter out NOT_APPLICABLE requirements
    requirements = [
        transform_requirement(req) for req in (result.requirements_checked or []) if req.status != "NOT_APPLICABLE"
    ]

    # Transform constituent drawings if present
    constituent_drawings = None
    if result.is_mixed_drawing and result.constituent_drawings:
        constituent_drawings = [transform_individual_drawing(drawing) for drawing in result.constituent_drawings]

    # Prefer humanised reasoning for user-friendly display, fall back to raw reasoning
    reasoning = getattr(result, "humanised_reasoning", None) or result.reasoning

    return ValidationResponse(
        document_id=document_id,
        document_type=normalise_document_type(result.document_type) or "OTHER_PLANS",
        validity=str(result.validity).upper(),
        confidence=str(result.confidence).upper(),
        reasoning=reasoning,
        requirements_checked=requirements,
        is_mixed_drawing=result.is_mixed_drawing,
        constituent_drawings=constituent_drawings,
        classification_thinking=result.classification_thinking,
        validation_thinking=result.validation_thinking,
        execution_time=result.execution_time,
        success=result.success,
        error_message=result.error_message,
        prompt_type=result.prompt_type,
        carbon_impact=transform_carbon_impact(result.carbon_impact),
    )
