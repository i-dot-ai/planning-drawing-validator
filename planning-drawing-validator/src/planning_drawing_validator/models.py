from dataclasses import dataclass

__all__ = [
    "Document",
    "ValidationResult",
    "Requirement",
    "IndividualDrawingResult",
    "CarbonImpact",
]


@dataclass(slots=True)
class CarbonImpact:
    """Carbon and environmental impact metrics from LLM inference.

    Captured from ecologits via i-dot-ai-utilities LiteLLMHandler.
    Values are ranges (min to max) as emissions vary by data centre location.

    Attributes:
        energy_kwh_min: Minimum electricity consumption in kilowatt-hours.
        energy_kwh_max: Maximum electricity consumption in kilowatt-hours.
        gwp_kgco2eq_min: Minimum global warming potential in kg CO2 equivalent.
        gwp_kgco2eq_max: Maximum global warming potential in kg CO2 equivalent.
        adpe_kgsbeq_min: Minimum abiotic resource depletion in kg Sb equivalent.
        adpe_kgsbeq_max: Maximum abiotic resource depletion in kg Sb equivalent.
        pe_mj_min: Minimum primary energy used in megajoules.
        pe_mj_max: Maximum primary energy used in megajoules.
        wcf_l_min: Minimum water consumption factor in litres.
        wcf_l_max: Maximum water consumption factor in litres.
    """

    energy_kwh_min: float
    energy_kwh_max: float
    gwp_kgco2eq_min: float
    gwp_kgco2eq_max: float
    adpe_kgsbeq_min: float
    adpe_kgsbeq_max: float
    pe_mj_min: float
    pe_mj_max: float
    wcf_l_min: float
    wcf_l_max: float


@dataclass(slots=True)
class Document:
    """A document to validate in production.

    Represents the minimal information needed to locate and validate a document.
    No ground truth, no expected results, no evaluation metadata.

    Attributes:
        document_id: Unique identifier for the document.
        filename: Original filename of the document.
        file_path: Optional local file path (for local filesystem storage).
        storage_key: Optional storage identifier (S3 key, Azure blob path, etc.)
            used when working with custom storage implementations.
    """

    document_id: str
    filename: str
    file_path: str | None = None
    storage_key: str | None = None


@dataclass(slots=True)
class Requirement:
    """Result of checking a single validation requirement.

    Attributes:
        requirement: Name or description of the requirement.
        status: Check result (PASS, FAIL, or NOT_APPLICABLE).
        details: Optional additional details about the check.
    """

    requirement: str
    status: str  # PASS, FAIL, NOT_APPLICABLE
    details: str | None = None


@dataclass(slots=True)
class IndividualDrawingResult:
    """Result for a single drawing within a mixed-drawing document.

    Attributes:
        drawing_type: Type of this individual drawing (SITE_PLAN, FLOOR_PLAN, etc.).
        validity: Validity assessment for this drawing.
        reasoning: LLM's reasoning for this drawing's assessment.
        confidence: Confidence level for this drawing.
        requirements_checked: List of requirements checked for this drawing.
        humanised_reasoning: User-friendly version of the reasoning (optional).
    """

    drawing_type: str
    validity: str
    reasoning: str
    confidence: str
    requirements_checked: list[Requirement]
    humanised_reasoning: str | None = None


@dataclass(slots=True)
class ValidationResult:
    """Production output from document validation.

    Contains classification and validation results for a single document.
    This is the primary output of the production document validator.

    No ground truth comparison, no accuracy metrics, no evaluation data.
    Just the validation result itself.

    Attributes:
        document_id: Unique identifier for the document.
        document_type: Classified document type (SITE_PLAN, FLOOR_PLAN, etc.).
        validity: Validity assessment (VALID, INVALID, CLARIFICATION_NEEDED).
        reasoning: LLM's detailed reasoning for the validity assessment.
        confidence: Confidence level (HIGH, MEDIUM, LOW).
        requirements_checked: List of individual requirement check results.
        execution_time: Time taken for validation in seconds.
        success: Whether validation completed successfully.
        error_message: Error details if validation failed.
        prompt_type: Type of validation prompt used.
        is_mixed_drawing: Whether this is a mixed drawing document (contains multiple drawings).
        constituent_drawings: Individual drawing results for mixed drawing documents.
        classification_confidence: Confidence level from classification stage (HIGH, MEDIUM, LOW).
        classification_reasoning: LLM's reasoning for the classification.
        classification_thinking: Gemini's extended thinking from classification stage (optional).
        validation_thinking: Gemini's extended thinking from validation stage (optional).
        carbon_impact: Environmental impact metrics from LLM inference (optional).
        humanised_reasoning: User-friendly version of the reasoning (optional).
    """

    document_id: str
    document_type: str
    validity: str
    reasoning: str
    confidence: str
    requirements_checked: list[Requirement]
    execution_time: float
    success: bool
    error_message: str | None = None
    prompt_type: str | None = None
    is_mixed_drawing: bool = False
    constituent_drawings: list[IndividualDrawingResult] | None = None
    classification_confidence: str | None = None
    classification_reasoning: str | None = None
    classification_thinking: str | None = None
    validation_thinking: str | None = None
    carbon_impact: CarbonImpact | None = None
    humanised_reasoning: str | None = None


def create_validation_result(
    *,
    document_id: str,
    document_type: str,
    validity: str,
    reasoning: str,
    confidence: str = "UNKNOWN",
    requirements_checked: list[Requirement] | None = None,
    execution_time: float = 0.0,
    success: bool = True,
    error_message: str | None = None,
    prompt_type: str | None = None,
) -> ValidationResult:
    """Factory function for creating ValidationResult instances.

    Provides keyword-only interface with sensible defaults.

    Args:
        document_id: Unique identifier for the document.
        document_type: Classified document type.
        validity: Validity assessment.
        reasoning: Detailed reasoning for assessment.
        confidence: Confidence level (default: UNKNOWN).
        requirements_checked: List of requirement checks (default: []).
        execution_time: Validation duration in seconds (default: 0.0).
        success: Whether validation succeeded (default: True).
        error_message: Error details if failed.
        prompt_type: Validation prompt type used.

    Returns:
        Configured ValidationResult instance.
    """
    return ValidationResult(
        document_id=document_id,
        document_type=document_type,
        validity=validity,
        reasoning=reasoning,
        confidence=confidence,
        requirements_checked=[
            Requirement(
                requirement=r["requirement"],
                status=r["status"],
                details=r.get("details"),
            )
            for r in (requirements_checked or [])
        ]
        if isinstance(requirements_checked, list)
        and requirements_checked
        and isinstance(requirements_checked[0], dict)
        else requirements_checked or [],
        execution_time=execution_time,
        success=success,
        error_message=error_message,
        prompt_type=prompt_type,
    )
