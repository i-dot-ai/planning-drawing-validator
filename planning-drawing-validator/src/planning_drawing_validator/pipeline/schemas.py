"""Pipeline schemas for classification and validation stages.

This module contains all Pydantic models for structured LLM outputs:
- Classification schemas: Document type identification and constituent drawing detection
- Validation schemas: Document-specific validation checks with evidence and criticality
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


# ============================================================================
# CLASSIFICATION SCHEMAS
# ============================================================================


class DocumentType(str, Enum):
    """Valid document types for classification."""

    SITE_PLAN = "site_plan"
    LOCATION_PLAN = "location_plan"
    ELEVATION = "elevation"
    FLOOR_PLAN = "floor_plan"
    SECTION_DRAWING = "section_drawing"
    ROOF_PLAN = "roof_plan"
    DETAIL_DRAWING = "detail_drawing"
    STREET_SCENE = "street_scene"
    SITE_LEVELS = "site_levels"
    SKETCH_PLAN = "sketch_plan"
    VISIBILITY_SPLAY = "visibility_splay"
    MIXED_PLANS = "mixed_plans"
    OTHER_PLANS = "other_plans"


class Confidence(str, Enum):
    """Confidence levels for classification."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConstituentDrawing(BaseModel):
    """Individual drawing within a mixed plan document."""

    drawing_type: DocumentType = Field(
        description="Type of this constituent drawing (cannot be mixed_plans, but other_plans is allowed for unclear content)"
    )
    description: str = Field(
        description="Brief description of this drawing (e.g., 'Ground floor plan showing existing layout', 'Front elevation')",
        min_length=10,
    )
    location_on_sheet: str = Field(
        description="Where this drawing appears (e.g., 'top left', 'bottom half', 'centre panel')"
    )

    @field_validator("drawing_type")
    @classmethod
    def validate_constituent_type(cls, v: DocumentType) -> DocumentType:
        """Ensure constituent drawings are not mixed_plans (recursive nesting not allowed)."""
        if v == DocumentType.MIXED_PLANS:
            raise ValueError("Constituent drawing cannot be mixed_plans (no recursive nesting).")
        # Allow other_plans for constituents that can't be specifically classified
        return v


class ClassificationResponse(BaseModel):
    """Classification stage output structure."""

    document_type: DocumentType = Field(
        description="""Classified document type based on visual analysis. Key discriminators:

- site_plan: Zoomed site layout at 1:200/1:500, shows property boundary, building positions, north arrow. Also known as "Block Plan"
- location_plan: OS map base at 1:1250/1:2500, wider context with multiple roads/buildings, red line boundary
- elevation: External face view of WHOLE BUILDING (front/rear/side/N/S/E/W), doors/windows visible, NO cut-through. Must show complete building facade, not isolated components
- floor_plan: Internal layout from above, rooms labelled, walls/doors/windows, storey level stated. NOTE: Floor plans often show external context (gardens, boundaries, spot levels) around the building - this is NORMAL and does NOT make it mixed_plans
- section_drawing: Cut-through view showing internal spatial relationships, hatched walls, floor levels, stair treads in cross-section. If titled "SECTION" but shows only external facade = elevation, not section
- roof_plan: Roof geometry from above (ridges, hips, valleys, chimneys), NOT floor layout
- detail_drawing: Component/junction scale (1:5/1:10/1:20), shows construction details. INCLUDES: window schedules, door schedules, fenestration details showing individual window/door TYPES rather than whole building. If drawing shows multiple window "Types" at detail scale = detail_drawing, NOT elevation
- street_scene: Row of buildings along street, comparative heights across multiple plots
- site_levels: Top-down plan emphasising levels (spot levels, contours) at 1:200/1:500
- sketch_plan: Simple/hand-drawn for TPO applications, shows trees (T1, T2...)
- visibility_splay: Access/junction sight triangles with dimensioned X/Y distances
- mixed_plans: Contains 2+ genuinely DIFFERENT drawing types on one sheet (e.g., floor plan + elevation side by side). NOT mixed if: (a) multiple drawings of SAME type (existing + proposed floor plans), (b) floor plan with surrounding site context, (c) elevation with site context
- other_plans: Use when no category fits or content too unclear"""
    )
    confidence: Confidence = Field(
        description="HIGH: Title and visuals clearly align with multiple strong discriminators. MEDIUM: One strong cue with supporting evidence. LOW: Conflicting signals, poor image quality, or insufficient discriminators"
    )
    reasoning: str = Field(
        description="Detailed reasoning: 1) What titles/labels are visible? 2) What does visual content show? 3) Do they match? 4) Which discriminators confirm the type?"
    )
    constituent_drawings: list[ConstituentDrawing] | None = Field(
        default=None,
        description="If document_type is mixed_plans, list all constituent drawing types present. Otherwise leave as None.",
    )

    @field_validator("constituent_drawings", mode="before")
    @classmethod
    def clean_constituent_list(cls, v: Any) -> Any:
        """Filter out None values from constituent_drawings list."""
        if v is None:
            return None
        if isinstance(v, list):
            # Filter out None values
            filtered = [item for item in v if item is not None]
            # Return None if list is empty after filtering
            return filtered if filtered else None
        return v

    @field_validator("constituent_drawings")
    @classmethod
    def validate_constituent_list(
        cls, v: list[ConstituentDrawing] | None, info: ValidationInfo
    ) -> list[ConstituentDrawing] | None:
        """Ensure constituent_drawings is populated only for mixed_plans."""
        values = info.data
        doc_type = values.get("document_type")

        if doc_type == DocumentType.MIXED_PLANS:
            if not v or len(v) < 2:
                raise ValueError(
                    "mixed_plans must have at least 2 constituent_drawings. "
                    "If only one drawing type present, classify as that type instead."
                )
        elif v is not None:
            raise ValueError(
                f"constituent_drawings should only be populated for mixed_plans, not {doc_type}"
            )

        return v

    @field_validator("document_type", mode="before")
    @classmethod
    def normalise_document_type(cls, value: Any) -> Any:
        """Normalise free-form model responses to supported enum values."""
        if isinstance(value, DocumentType):
            return value

        if isinstance(value, str):
            normalised = value.strip().lower().replace(" ", "_")

            # Map common variants to canonical enum values
            mapping = {
                "siteplan": "site_plan",
                "site_plan": "site_plan",
                "locationplan": "location_plan",
                "location_plan": "location_plan",
                "floorplan": "floor_plan",
                "floor_plan": "floor_plan",
                "elevation": "elevation",
                "section": "section_drawing",
                "section_drawing": "section_drawing",
                "roof_plan": "roof_plan",
                "roofplan": "roof_plan",
                "detail_drawing": "detail_drawing",
                "detaildrawing": "detail_drawing",
                "mixed": "mixed_plans",
                "mixed_plans": "mixed_plans",
                "other_plan": "other_plans",
                "other_plans": "other_plans",
                "other": "other_plans",
            }

            mapped = mapping.get(normalised)
            if mapped:
                return mapped

        return value


# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================


class ValidationCheck(BaseModel):
    """Universal validation check format.

    Used for all validation requirements. The evidence field should contain
    specific observable details about what was found or why it's missing.
    """

    status: str = Field(
        description="Check status",
        pattern="^(COMPLIANT|PRESENT|MISSING|UNCLEAR|NOT_APPLICABLE)$",
    )
    value: str | None = Field(
        default=None,
        description="Extracted value if applicable (e.g., '1:100', 'PROPOSED', address)",
    )
    evidence: str = Field(description="Specific observable evidence for this check", min_length=5)
    critical: bool = Field(
        description="Whether this check is critical for document validity (critical checks failing = INVALID document)"
    )


class SectionValidationChecks(BaseModel):
    """Validation checks for section drawings."""

    scale: ValidationCheck = Field(
        description="""VALID SCALES: 1:50, 1:100, 1:200, 1:500 ONLY.
INVALID SCALES (mark as MISSING): 1:75, 1:25, 1:150, or any other non-standard scale.

BOTH required for COMPLIANT:
1. Scale TEXT showing a valid scale value
2. Linear scale BAR (graduated ruler with tick marks)

If scale is non-standard (e.g., 1:75) = MISSING (incorrect scale).
If scale text present but NO scale bar = PRESENT.""",
        json_schema_extra={"critical": True},
    )
    cut_indicators: ValidationCheck = Field(
        description="Must show clear cut-through view with internal spatial relationships (stair treads, floor levels, section markers, hatch patterns)",
        json_schema_extra={"critical": False},
    )
    floor_levels: ValidationCheck = Field(
        description="Floor levels and heights should be indicated (level markers, height dimensions, floor-to-floor measurements)",
        json_schema_extra={"critical": False},
    )
    site_levels: ValidationCheck = Field(
        description="Ground/site levels should be indicated (ground level markers, datum references, relationship to finished ground)",
        json_schema_extra={"critical": False},
    )
    neighbouring_relationship: ValidationCheck = Field(
        description="Relationship to adjacent structures should be shown (neighbouring buildings, party walls, proximity context)",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification must be present (address, project name, or site description)",
        json_schema_extra={"critical": False},
    )
    state_labelling: ValidationCheck = Field(
        description="""EXISTING/PROPOSED state must be clearly and CONSISTENTLY labelled.
CRITICAL: If title says 'EXISTING' but content shows 'PROPOSED' (or vice versa) = MISSING (inconsistent labelling is INVALID).
Check: main title, individual drawing labels, and filename must all align. References to 'existing levels' within proposed drawings is acceptable context.""",
        json_schema_extra={"critical": True},
    )


class FloorPlanValidationChecks(BaseModel):
    """Validation checks for floor plans."""

    scale: ValidationCheck = Field(
        description="""Must be exactly 1:50 or 1:100. BOTH required for COMPLIANT:
1. Scale TEXT (e.g., "1:100", "Scale 1:50")
2. Linear scale BAR (graduated ruler with tick marks and measurements, e.g., 0-5-10m)
If scale text present but NO scale bar = PRESENT (not COMPLIANT)""",
        json_schema_extra={"critical": True},
    )
    floor_level: ValidationCheck = Field(
        description="""CRITICAL VISUAL CROSS-CHECK - Labels are often WRONG.

LOFT/ATTIC DETECTION (commonly mislabelled as "First Floor"):
- If on same sheet as a ROOF PLAN directly below/adjacent, it's likely LOFT not first floor
- Skylights, roof windows, Velux windows = LOFT indicator
- Sloped ceiling lines or reduced headroom annotations = LOFT
- Dormer windows shown in plan = LOFT
- Room positioned directly under visible roof geometry = LOFT

FLOOR INDICATORS:
- Ground floor: Main entrance, garden access, no stairs down
- First floor: Above ground floor, stairs up from below, typically over ground floor rooms
- Loft/Attic: Topmost level under roof, skylights, sloped areas, often smaller footprint

COMMON ERROR TO CATCH:
If sheet shows "First Floor Plan" PLUS "Roof Plan", and the floor plan rooms sit directly under the roof = this is LOFT mislabelled as First Floor → MISSING

EVIDENCE: "Visual shows: [ground/first/loft characteristics]. Roof plan on same sheet: [yes/no]. Label claims: [X]. Match: [yes/no]".""",
        json_schema_extra={"critical": True},
    )
    external_context: ValidationCheck = Field(
        description="Check if gardens/boundaries/outdoor areas shown. If external context present, north arrow becomes mandatory",
        json_schema_extra={"critical": False},
    )
    north_arrow: ValidationCheck = Field(
        description="""North arrow symbol - ASSUME REQUIRED unless plan shows ONLY internal rooms.

DEFAULT: North arrow IS required. Only mark NOT_APPLICABLE if the plan shows ZERO external elements.

EXTERNAL CONTEXT (if ANY visible, north arrow required):
- Garden, patio, terrace, lawn areas
- Property boundaries, fences, walls
- Neighbouring buildings (even as outlines)
- External levels, spot heights
- Driveways, paths, parking
- Trees, vegetation

CRITICAL: If the plan shows the building outline with ANY surrounding context, north arrow is REQUIRED.
NOT_APPLICABLE only if: Plan shows purely internal room layout with NO external surroundings whatsoever.

STATUS:
- COMPLIANT: North arrow symbol clearly visible (arrow/compass, not just 'N' text)
- MISSING: External context visible but no north arrow found
- NOT_APPLICABLE: Plan shows only internal rooms, no external context at all (RARE)

EVIDENCE: "External context: [none / garden visible / boundary shown / etc]. North arrow: [found at location X / not found]".""",
        json_schema_extra={"critical": True},
    )
    room_labels: ValidationCheck = Field(
        description="Room uses should be indicated on plan or in linked schedule. Existing plans may have minimal labelling if building use clear from context",
        json_schema_extra={"critical": False},
    )
    dimensions: ValidationCheck = Field(
        description="Key dimensions should be shown",
        json_schema_extra={"critical": False},
    )
    door_swings: ValidationCheck = Field(
        description="Door swing directions should be indicated",
        json_schema_extra={"critical": False},
    )
    extension_area_metric: ValidationCheck = Field(
        description="If extension/additional floors shown: explicit area metric (m²) required. If no extension: NOT_APPLICABLE",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="""Full site address required for planning purposes.

STATUS GUIDE:
- COMPLIANT: Property number + street name clearly visible (e.g., '71 Clarence Ave', '14 Union Road')
- PRESENT: Street name visible but NO property number (e.g., 'Union Road' alone)
- MISSING: No address information, or only project name/client name visible

In evidence: State exactly what address text you found.""",
        json_schema_extra={"critical": True},
    )
    state_labelling: ValidationCheck = Field(
        description="EXISTING/PROPOSED state must be clearly and explicitly labelled. Generic labels without state = MISSING",
        json_schema_extra={"critical": True},
    )


class ElevationValidationChecks(BaseModel):
    """Validation checks for elevations."""

    scale: ValidationCheck = Field(
        description="""Must be exactly 1:50 or 1:100. BOTH required for COMPLIANT:
1. Scale TEXT (e.g., "1:100", "Scale 1:50")
2. Linear scale BAR (graduated ruler with tick marks and measurements, e.g., 0-5-10m)
If scale text present but NO scale bar = PRESENT (not COMPLIANT). All other scales invalid (1:20, 1:25, 1:75, 1:200)""",
        json_schema_extra={"critical": True},
    )
    face_labelling: ValidationCheck = Field(
        description="""MANDATORY VISUAL VERIFICATION - Labels are often WRONG.

YOUR TASK: Determine if what the drawing SHOWS matches what the label CLAIMS.

BEFORE marking COMPLIANT, you MUST identify in the drawing:
- Is there a main entrance door visible? (indicates FRONT)
- Is there a garden/patio/rear extension visible? (indicates REAR)
- Is it a narrow gable end with few windows? (indicates SIDE)

COMMON LABELLING ERRORS YOU MUST CATCH:
- Drawing shows garden/patio but label says "FRONT" → MISSING (mislabelled)
- Drawing shows main entrance but label says "REAR" → MISSING (mislabelled)
- Filename says "REAR" but title says "FRONT" → MISSING (inconsistent)

STATUS:
- COMPLIANT: Visual features match the label claim
- MISSING: Visual features contradict the label (THIS IS THE ERROR TO CATCH)

EVIDENCE FORMAT (mandatory):
"I see: [entrance door / garden / gable end / etc]. Label says: [FRONT/REAR/SIDE]. Verdict: [match/mismatch]"

If you cannot clearly identify front vs rear features, use status=UNCLEAR and confidence=MEDIUM.""",
        json_schema_extra={"critical": True},
    )
    external_view: ValidationCheck = Field(
        description="Must be external elevation view, not section cut-through",
        json_schema_extra={"critical": False},
    )
    site_context_north_arrow: ValidationCheck = Field(
        description="""North arrow - DEFAULT TO REQUIRED for multi-elevation sheets.

ASSUME REQUIRED if the sheet shows multiple elevations (front/rear/side) as orientation context is critical.

SITE CONTEXT INDICATORS (any = north arrow required):
- Multiple elevations on one sheet showing different faces
- Neighbouring properties visible (even partially)
- Boundary walls, fences, or site edges shown
- Ground level lines or external levels marked
- Any text referencing compass directions (N/S/E/W facing)

STATUS:
- COMPLIANT: North arrow symbol visible
- MISSING: Multiple elevations shown OR site context visible, but no north arrow
- NOT_APPLICABLE: Single elevation showing ONLY the subject building with zero surroundings (RARE)

EVIDENCE: "Sheet shows: [single elevation / multiple elevations]. Site context: [none / neighbours visible / etc]. North arrow: [found / not found]".""",
        json_schema_extra={"critical": True},
    )
    materials: ValidationCheck = Field(
        description="Materials should be indicated",
        json_schema_extra={"critical": False},
    )
    windows_doors: ValidationCheck = Field(
        description="Window and door openings must be clearly depicted",
        json_schema_extra={"critical": False},
    )
    building_form: ValidationCheck = Field(
        description="Overall building shape and massing must be shown",
        json_schema_extra={"critical": False},
    )
    ground_line: ValidationCheck = Field(
        description="Relationship to ground level should be shown",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="""Full site address required for planning purposes.

STATUS GUIDE:
- COMPLIANT: Property number + street name clearly visible (e.g., '71 Clarence Ave', '14 Union Road', '62 Mordaunt Street')
- PRESENT: Street name visible but NO property number (e.g., 'Union Road' alone, 'Clarence Avenue Development')
- MISSING: No address information, or only project name/client name visible

COMMON ERRORS (mark as PRESENT, not COMPLIANT):
- 'Union Road' without number = PRESENT
- 'The Smith Residence' = PRESENT (no address)
- 'Plot 4, Development Site' = PRESENT (no street address)

In evidence: State exactly what address text you found.""",
        json_schema_extra={"critical": True},
    )
    state_labelling: ValidationCheck = Field(
        description="""EXISTING/PROPOSED state must be clearly and CONSISTENTLY labelled.
CRITICAL: If title says 'EXISTING' but drawing shows proposed changes (or vice versa) = MISSING.
If filename says one state but drawing shows another = MISSING (inconsistent labelling is INVALID).""",
        json_schema_extra={"critical": True},
    )


class LocationPlanValidationChecks(BaseModel):
    """Validation checks for location plans."""

    scale: ValidationCheck = Field(
        description="""Must be exactly 1:1250 or 1:2500. BOTH required for COMPLIANT:
1. Scale TEXT (e.g., "1:1250")
2. Linear scale BAR (graduated ruler with measurements)
If scale text present but NO scale bar = PRESENT (not COMPLIANT). All other scales invalid (1:1000, 1:2000, 1:500, 1:200)""",
        json_schema_extra={"critical": True},
    )
    red_line_boundary: ValidationCheck = Field(
        description="""A red line boundary must be a VISIBLE RED-COLORED LINE drawn on the map.
DO NOT confuse with: "R.L." text (usually means Road Level), property boundary markings, or other annotations.

WHAT TO LOOK FOR: An actual continuous red line enclosing the application site.

REQUIRED EXTENT: building + ALL curtilage (gardens, driveways, parking areas) + access route to public highway.

STATUS GUIDE:
- COMPLIANT: Visible red line clearly encompasses full property boundary including gardens/curtilage AND connects to public road
- PRESENT: Red line exists but only around building footprint, not full site extent
- MISSING: No actual red line visible (text annotations like "R.L." do NOT count), or line doesn't enclose the site

In evidence, describe: "Red line visible: [yes/no]. If yes, extent covers: [building only / full site with curtilage]".""",
        json_schema_extra={"critical": True},
    )
    access_highway: ValidationCheck = Field(
        description="Name of public highway providing access should be shown",
        json_schema_extra={"critical": False},
    )
    map_currency: ValidationCheck = Field(
        description="Should show recent OS copyright marks indicating current map",
        json_schema_extra={"critical": False},
    )
    surrounding_context: ValidationCheck = Field(
        description="Must show minimum 50m radius with multiple roads and buildings for context",
        json_schema_extra={"critical": False},
    )
    north_arrow: ValidationCheck = Field(
        description="North arrow symbol must be present (not just text). Critical for all location plans",
        json_schema_extra={"critical": True},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification must be present (address, project name, or site description)",
        json_schema_extra={"critical": False},
    )


class SitePlanValidationChecks(BaseModel):
    """Validation checks for site/block plans."""

    scale: ValidationCheck = Field(
        description="""Must be exactly 1:200 or 1:500. BOTH required for COMPLIANT:
1. Scale TEXT (e.g., "1:200", "Scale 1:500")
2. Linear scale BAR (graduated ruler with tick marks and measurements, e.g., 0-10-20m)
If scale text present but NO scale bar = PRESENT (not COMPLIANT)""",
        json_schema_extra={"critical": True},
    )
    state_labelling: ValidationCheck = Field(
        description="Main title must explicitly state EXISTING or PROPOSED state. Acceptable formats: 'EXISTING SITE PLAN', 'PROPOSED SITE PLAN', 'EXISTING BLOCK PLAN', 'PROPOSED BLOCK PLAN'. The key requirement is explicit EXISTING/PROPOSED - 'Block Plan' is equivalent to 'Site Plan'",
        json_schema_extra={"critical": True},
    )
    north_arrow: ValidationCheck = Field(
        description="North arrow symbol required (compass rose or 'N' with arrow). Plain text without arrow not acceptable",
        json_schema_extra={"critical": True},
    )
    property_boundary: ValidationCheck = Field(
        description="Property boundary must be clearly shown",
        json_schema_extra={"critical": False},
    )
    building_positions: ValidationCheck = Field(
        description="Building positions, sizes, and uses should be indicated",
        json_schema_extra={"critical": False},
    )
    adjacent_streets: ValidationCheck = Field(
        description="Adjacent streets and access arrangements should be shown",
        json_schema_extra={"critical": False},
    )
    red_line_boundary: ValidationCheck = Field(
        description="If red line shown: must encompass building + curtilage + access to public highway. Red line extent critical if present",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification recommended but not mandatory",
        json_schema_extra={"critical": False},
    )


class RoofPlanValidationChecks(BaseModel):
    """Validation checks for roof plans."""

    scale: ValidationCheck = Field(
        description="""Must be exactly 1:50 or 1:100. BOTH required for COMPLIANT:
1. Scale TEXT (e.g., "1:100")
2. Linear scale BAR (graduated ruler with tick marks)
If scale text present but NO scale bar = PRESENT (not COMPLIANT)""",
        json_schema_extra={"critical": True},
    )
    state_labelling: ValidationCheck = Field(
        description="EXISTING/PROPOSED state must be clearly labelled",
        json_schema_extra={"critical": True},
    )
    roof_features: ValidationCheck = Field(
        description="Must show roof features from above (roof geometry, ridges, hips, valleys, slopes), not floor layout",
        json_schema_extra={"critical": False},
    )
    roof_geometry: ValidationCheck = Field(
        description="Roof geometry (ridges, hips, valleys, slopes) should be shown",
        json_schema_extra={"critical": False},
    )
    roof_windows: ValidationCheck = Field(
        description="Roof windows (rooflights, dormers, skylights, chimneys, access hatches) should be indicated if applicable",
        json_schema_extra={"critical": False},
    )
    materials: ValidationCheck = Field(
        description="Roof covering materials should be indicated. For existing-only plans, materials not instant-invalid if missing",
        json_schema_extra={"critical": False},
    )
    dimensions: ValidationCheck = Field(
        description="Roof dimensions, ridge heights, and levels should be shown",
        json_schema_extra={"critical": False},
    )
    north_arrow: ValidationCheck = Field(
        description="""North arrow symbol ALWAYS required for roof plans - no exceptions.
Must be a graphic symbol (arrow/compass), not just text 'N'.
If no north arrow visible = MISSING. Do NOT mark as NOT_APPLICABLE for roof plans.""",
        json_schema_extra={"critical": True},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification should be present",
        json_schema_extra={"critical": False},
    )


class DetailDrawingValidationChecks(BaseModel):
    """Validation checks for detail drawings."""

    scale: ValidationCheck = Field(
        description="Must be 1:5, 1:10, 1:20 (or 1:1/1:2 for traditional joinery). Mixed scales acceptable if each sub-drawing clearly labelled",
        json_schema_extra={"critical": False},
    )
    component_detail: ValidationCheck = Field(
        description="Must show component/junction detail at component scale (window jambs, eaves, joinery, junctions). Exception: 'Existing Windows Elevations' at component scale with dimensions acceptable even without full junction details",
        json_schema_extra={"critical": False},
    )
    construction_information: ValidationCheck = Field(
        description="Construction method/assembly and materials should be indicated. For existing-only details: material callouts not mandatory if adequately dimensioned",
        json_schema_extra={"critical": False},
    )
    dimensional_information: ValidationCheck = Field(
        description="Clear dimensioning or proportional relationships required. 'DO NOT SCALE' disclaimers acceptable when scale and/or dimensions provided",
        json_schema_extra={"critical": False},
    )
    drawing_clarity: ValidationCheck = Field(
        description="Clear drawing title and type identification required. Multiple sub-drawings acceptable with mixed scales if each clearly labelled",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification recommended but not mandatory if drawing clearly part of submitted set",
        json_schema_extra={"critical": False},
    )
    state_labelling: ValidationCheck = Field(
        description="""EXISTING or PROPOSED state must be explicitly labelled in title or drawing.
If showing both existing and proposed (e.g., 'Existing & Proposed Window Detail'), both must be clearly distinguished.
If no state label visible = MISSING.""",
        json_schema_extra={"critical": True},
    )


class GenericValidationChecks(BaseModel):
    """Generic validation checks for documents without specific schemas."""

    scale: ValidationCheck = Field(
        description="Scale should be explicitly stated and appropriate",
        json_schema_extra={"critical": False},
    )
    site_identification: ValidationCheck = Field(
        description="Site identification should be present",
        json_schema_extra={"critical": False},
    )
    state_labelling: ValidationCheck = Field(
        description="EXISTING/PROPOSED state should be clearly labelled if applicable",
        json_schema_extra={"critical": False},
    )
    drawing_clarity: ValidationCheck = Field(
        description="Drawing should have clear title, labels, and be legible",
        json_schema_extra={"critical": False},
    )


# Mapping of document types to their validation check models
VALIDATION_CHECK_MODELS: dict[str, type[BaseModel]] = {
    "section_drawing": SectionValidationChecks,
    "floor_plan": FloorPlanValidationChecks,
    "elevation": ElevationValidationChecks,
    "location_plan": LocationPlanValidationChecks,
    "site_plan": SitePlanValidationChecks,
    "roof_plan": RoofPlanValidationChecks,
    "detail_drawing": DetailDrawingValidationChecks,
    "general": GenericValidationChecks,
}


def create_validation_response_model(check_model: type[BaseModel]) -> type[BaseModel]:
    """Create a ValidationResponse model with typed validation_checks field.

    Args:
        check_model: The type-specific check model (e.g., FloorPlanValidationChecks)

    Returns:
        A ValidationResponse model with properly typed validation_checks
    """

    class ValidationResponse(BaseModel):
        """Complete validation response structure."""

        validity_assessment: str = Field(
            description="Overall validity assessment", pattern="^(VALID|INVALID)$"
        )
        overall_confidence: str = Field(
            description="Confidence level of the assessment",
            pattern="^(HIGH|MEDIUM|LOW)$",
        )
        assessment_reasoning: str = Field(
            description="Detailed reasoning for the overall assessment"
        )
        validation_checks: check_model = Field(  # type: ignore[valid-type]
            description="Document-specific validation checks"
        )

        @field_validator("validity_assessment", mode="before")
        @classmethod
        def normalize_validity(cls, v: Any) -> str:
            """Normalize validity assessment - some models return COMPLIANT instead of VALID."""
            if isinstance(v, str):
                v_upper = v.upper().strip()
                # Map COMPLIANT/PRESENT to VALID (model confusion with check status terms)
                if v_upper in ("COMPLIANT", "PRESENT", "PASS", "PASSED", "OK"):
                    return "VALID"
                # Map non-compliant terms to INVALID
                if v_upper in (
                    "NON-COMPLIANT",
                    "NONCOMPLIANT",
                    "MISSING",
                    "FAIL",
                    "FAILED",
                ):
                    return "INVALID"
                return v_upper
            return v

    return ValidationResponse
