from pydantic import BaseModel, Field


class RequirementCheck(BaseModel):
    """Individual requirement validation result."""

    requirement: str = Field(
        description="Name of the requirement being checked",
        examples=["North arrow present"],
    )
    status: str = Field(
        description="Result of the requirement check",
        examples=["PASS"],
        pattern="^(PASS|FAIL|UNCLEAR)$",
    )
    details: str | None = Field(
        default=None,
        description="Additional context about the check result",
        examples=["Clear north arrow found in top right corner"],
    )


class IndividualDrawing(BaseModel):
    """Validation result for a single drawing within a mixed document."""

    drawing_type: str = Field(
        description="Type of this individual drawing",
        examples=["FLOOR_PLAN"],
        pattern="^(SITE_PLAN|FLOOR_PLAN|ELEVATION|SECTION|ROOF_PLAN|LOCATION_PLAN|DETAIL_DRAWING)$",
    )
    validity: str = Field(
        description="Validity assessment for this drawing",
        examples=["VALID"],
        pattern="^(VALID|INVALID|CLARIFICATION_NEEDED)$",
    )
    confidence: str = Field(
        description="AI confidence level in this assessment",
        examples=["HIGH"],
        pattern="^(HIGH|MEDIUM|LOW)$",
    )
    reasoning: str = Field(
        description="Explanation of the validation decision (user-friendly if humanised)",
        examples=["Floor plan shows all rooms clearly labeled with dimensions"],
    )
    requirements_checked: list[RequirementCheck] = Field(
        description="List of requirements validated for this drawing",
        default_factory=list,
    )


class CarbonImpact(BaseModel):
    """Environmental impact metrics from LLM inference.

    Values are ranges (min to max) as emissions vary by data centre location and energy sources.
    Tracked via ecologits library integrated with LiteLLM.
    """

    energy_kwh_min: float = Field(
        description="Minimum electricity consumption in kilowatt-hours",
        examples=[0.000123],
    )
    energy_kwh_max: float = Field(
        description="Maximum electricity consumption in kilowatt-hours",
        examples=[0.000156],
    )
    gwp_kgco2eq_min: float = Field(
        description="Minimum global warming potential in kg CO2 equivalent",
        examples=[0.000045],
    )
    gwp_kgco2eq_max: float = Field(
        description="Maximum global warming potential in kg CO2 equivalent",
        examples=[0.000067],
    )
    adpe_kgsbeq_min: float = Field(
        description="Minimum abiotic resource depletion in kg Sb equivalent",
        examples=[0.00000012],
    )
    adpe_kgsbeq_max: float = Field(
        description="Maximum abiotic resource depletion in kg Sb equivalent",
        examples=[0.00000018],
    )
    pe_mj_min: float = Field(description="Minimum primary energy used in megajoules", examples=[0.00234])
    pe_mj_max: float = Field(description="Maximum primary energy used in megajoules", examples=[0.00298])
    wcf_l_min: float = Field(description="Minimum water consumption factor in litres", examples=[0.00123])
    wcf_l_max: float = Field(description="Maximum water consumption factor in litres", examples=[0.00156])


class ValidationResponse(BaseModel):
    """Complete validation response structure."""

    document_id: str = Field(
        description="Unique identifier for this validation request",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    document_type: str = Field(
        description="Identified type of the planning drawing",
        examples=["FLOOR_PLAN"],
        pattern="^(SITE_PLAN|FLOOR_PLAN|ELEVATION|SECTION|MIXED|LOCATION_PLAN|ROOF_PLAN|DETAIL_DRAWING|OTHER_PLANS)$",
    )
    validity: str = Field(
        description="Overall validity assessment of the drawing",
        examples=["VALID"],
        pattern="^(VALID|INVALID|CLARIFICATION_NEEDED)$",
    )
    confidence: str = Field(
        description="AI confidence level in classification and validation",
        examples=["HIGH"],
        pattern="^(HIGH|MEDIUM|LOW)$",
    )
    reasoning: str = Field(
        description="Detailed explanation of the validation decision",
        examples=["The drawing contains all required elements including scale, north arrow, and clear labels"],
    )
    requirements_checked: list[RequirementCheck] = Field(
        description="List of requirements validated against the drawing",
        default_factory=list,
    )
    is_mixed_drawing: bool = Field(
        description="Whether the document contains multiple drawing types",
        default=False,
        examples=[False],
    )
    constituent_drawings: list[IndividualDrawing] | None = Field(
        default=None, description="Individual drawings if this is a mixed document"
    )
    execution_time: float | None = Field(default=None, description="Processing time in seconds", examples=[2.34])
    success: bool = Field(
        description="Whether the validation completed successfully",
        default=True,
        examples=[True],
    )
    error_message: str | None = Field(default=None, description="Error details if validation failed")
    prompt_type: str | None = Field(
        default=None,
        description="Type of validation prompt used",
        examples=["floor_plan_validation"],
    )
    carbon_impact: CarbonImpact | None = Field(
        default=None,
        description="Environmental impact metrics from LLM inference (energy, CO2, resource depletion)",
    )
    classification_thinking: str | None = Field(
        default=None,
        description="Gemini's extended thinking from classification stage (shows AI reasoning process)",
    )
    validation_thinking: str | None = Field(
        default=None,
        description="Gemini's extended thinking from validation stage (shows AI reasoning process)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_type": "FLOOR_PLAN",
                "validity": "VALID",
                "confidence": "HIGH",
                "reasoning": "Floor plan contains all required elements: scale 1:100, floor level clearly marked as GROUND FLOOR, room labels present, dimensions shown, and north arrow visible.",
                "requirements_checked": [
                    {
                        "requirement": "Scale indicated",
                        "status": "PASS",
                        "details": "Scale 1:100 clearly marked with both text and scale bar",
                    },
                    {
                        "requirement": "Floor level identified",
                        "status": "PASS",
                        "details": "Explicitly labeled as GROUND FLOOR",
                    },
                    {
                        "requirement": "Room labels present",
                        "status": "PASS",
                        "details": "All rooms labeled: Living Room, Kitchen, Bedroom, etc.",
                    },
                ],
                "is_mixed_drawing": False,
                "constituent_drawings": None,
                "execution_time": 2.34,
                "success": True,
                "error_message": None,
                "prompt_type": "floor_plan_validation",
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service health status", examples=["healthy"])
    service: str = Field(description="Service name", examples=["production-validation-api"])
    version: str = Field(description="API version", examples=["1.0.0"])


class ErrorResponse(BaseModel):
    """Error response structure."""

    detail: str = Field(
        description="Error message describing what went wrong",
        examples=["Validation failed: Invalid file format"],
    )
