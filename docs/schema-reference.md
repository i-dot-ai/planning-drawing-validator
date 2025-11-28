# Schema Reference

This document describes the data models used throughout the Planning Drawing Validator.

## Table of Contents

- [Input/Output Models](#inputoutput-models)
  - [Document](#document)
  - [ValidationResult](#validationresult)
  - [Requirement](#requirement)
  - [CarbonImpact](#carbonimpact)
- [Classification Schemas](#classification-schemas)
  - [DocumentType](#documenttype)
  - [Confidence](#confidence)
  - [ClassificationResponse](#classificationresponse)
- [Validation Schemas](#validation-schemas)
  - [ValidationCheck](#validationcheck)
  - [Type-Specific Checks](#type-specific-checks)

---

## Input/Output Models

### Document

Input model representing a document to validate.

```python
@dataclass
class Document:
    document_id: str           # Unique identifier
    filename: str              # Original filename
    file_path: str | None      # Local file path (optional)
    storage_key: str | None    # Cloud storage identifier (optional)
```

**Usage:**
```python
from planning_drawing_validator import Document

# Local file
doc = Document(
    document_id="site-plan-001",
    filename="site-plan.pdf",
    file_path="/path/to/site-plan.pdf"
)

# Cloud storage
doc = Document(
    document_id="site-plan-001",
    filename="site-plan.pdf",
    storage_key="planning-docs/site-plan.pdf"
)
```

### ValidationResult

Output model containing validation results.

```python
@dataclass
class ValidationResult:
    document_id: str                    # Unique identifier
    document_type: str                  # Classified type (SITE_PLAN, etc.)
    validity: str                       # VALID, INVALID, or CLARIFICATION_NEEDED
    reasoning: str                      # Detailed reasoning
    confidence: str                     # HIGH, MEDIUM, or LOW
    requirements_checked: list[Requirement]  # Individual checks
    execution_time: float               # Seconds
    success: bool                       # Validation completed
    error_message: str | None           # Error details if failed
    prompt_type: str | None             # Validation prompt type used
    is_mixed_drawing: bool              # Contains multiple drawing types
    constituent_drawings: list[IndividualDrawingResult] | None
    classification_confidence: str | None
    classification_reasoning: str | None
    classification_thinking: str | None  # Model reasoning (where supported)
    validation_thinking: str | None      # Model reasoning (where supported)
    carbon_impact: CarbonImpact | None   # Environmental metrics
```

### Requirement

Individual validation requirement check result.

```python
@dataclass
class Requirement:
    requirement: str      # Name of the requirement
    status: str           # PASS, FAIL, or NOT_APPLICABLE
    details: str | None   # Additional details
```

### CarbonImpact

Environmental impact metrics from LLM inference (via ecologits).

```python
@dataclass
class CarbonImpact:
    energy_kwh_min: float       # Min electricity (kWh)
    energy_kwh_max: float       # Max electricity (kWh)
    gwp_kgco2eq_min: float      # Min CO2 equivalent (kg)
    gwp_kgco2eq_max: float      # Max CO2 equivalent (kg)
    adpe_kgsbeq_min: float      # Min resource depletion (kg Sb eq)
    adpe_kgsbeq_max: float      # Max resource depletion (kg Sb eq)
    pe_mj_min: float            # Min primary energy (MJ)
    pe_mj_max: float            # Max primary energy (MJ)
```

---

## Classification Schemas

### DocumentType

Enum of supported document types.

| Value | Description |
|-------|-------------|
| `site_plan` | Property layout at 1:200/1:500, boundaries, building positions |
| `location_plan` | OS map base at 1:1250/1:2500, wider context, red line boundary |
| `elevation` | External face view of building (front/rear/side) |
| `floor_plan` | Internal layout from above, rooms labelled |
| `section_drawing` | Cut-through view showing internal spatial relationships |
| `roof_plan` | Roof geometry from above (ridges, hips, valleys) |
| `detail_drawing` | Component/junction details at 1:5/1:10/1:20 |
| `street_scene` | Row of buildings along street, comparative heights |
| `site_levels` | Top-down plan emphasising levels (spot levels, contours) |
| `sketch_plan` | Simple/hand-drawn for TPO applications |
| `visibility_splay` | Access/junction sight triangles |
| `mixed_plans` | Contains 2+ different drawing types on one sheet |
| `other_plans` | Unclassifiable or unclear content |

### Confidence

Confidence levels for assessments.

| Value | Description |
|-------|-------------|
| `HIGH` | Title and visuals clearly align with multiple strong discriminators |
| `MEDIUM` | One strong cue with supporting evidence |
| `LOW` | Conflicting signals, poor image quality, or insufficient discriminators |

### ClassificationResponse

LLM output from classification stage.

```python
class ClassificationResponse(BaseModel):
    document_type: DocumentType       # Classified type
    confidence: Confidence            # Classification confidence
    reasoning: str                    # Detailed reasoning
    constituent_drawings: list[ConstituentDrawing] | None  # For mixed_plans only
```

**ConstituentDrawing** (for mixed plans):
```python
class ConstituentDrawing(BaseModel):
    drawing_type: DocumentType   # Type (cannot be mixed_plans)
    description: str             # Brief description
    location_on_sheet: str       # Position (e.g., "top left")
```

---

## Validation Schemas

### ValidationCheck

Universal format for individual validation checks.

```python
class ValidationCheck(BaseModel):
    status: str          # COMPLIANT, PRESENT, MISSING, UNCLEAR, NOT_APPLICABLE
    value: str | None    # Extracted value (e.g., "1:100")
    evidence: str        # Observable evidence for this check
    critical: bool       # Whether failing invalidates the document
```

**Status Values:**
| Status | Meaning |
|--------|---------|
| `COMPLIANT` | Requirement fully met |
| `PRESENT` | Partially met (e.g., scale text without scale bar) |
| `MISSING` | Requirement not satisfied |
| `UNCLEAR` | Cannot determine from document |
| `NOT_APPLICABLE` | Requirement doesn't apply to this document |

### Type-Specific Checks

Each document type has specific validation requirements. Critical checks (marked with `critical: True`) must pass for the document to be valid.

#### SitePlanValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Must be 1:200 or 1:500 with scale bar |
| `state_labelling` | Yes | EXISTING/PROPOSED clearly stated |
| `north_arrow` | Yes | North arrow symbol present |
| `property_boundary` | No | Property boundary clearly shown |
| `building_positions` | No | Building positions and sizes indicated |
| `adjacent_streets` | No | Adjacent streets and access shown |
| `red_line_boundary` | No | Red line extent if present |
| `site_identification` | No | Address or site description |

#### LocationPlanValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Must be 1:1250 or 1:2500 with scale bar |
| `red_line_boundary` | Yes | Red line encompassing full site extent |
| `north_arrow` | Yes | North arrow symbol present |
| `access_highway` | No | Name of public highway shown |
| `map_currency` | No | Recent OS copyright marks |
| `surrounding_context` | No | Minimum 50m radius context |
| `site_identification` | No | Address or site description |

#### FloorPlanValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Must be 1:50 or 1:100 with scale bar |
| `floor_level` | Yes | Correct floor level labelling |
| `north_arrow` | Yes | Required if external context shown |
| `site_identification` | Yes | Full property address |
| `state_labelling` | Yes | EXISTING/PROPOSED clearly stated |
| `external_context` | No | Gardens/boundaries shown |
| `room_labels` | No | Room uses indicated |
| `dimensions` | No | Key dimensions shown |
| `door_swings` | No | Door swing directions indicated |
| `extension_area_metric` | No | Area metric for extensions |

#### ElevationValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Must be 1:50 or 1:100 with scale bar |
| `face_labelling` | Yes | Correct front/rear/side labelling |
| `site_context_north_arrow` | Yes | Required for multi-elevation sheets |
| `site_identification` | Yes | Full property address |
| `state_labelling` | Yes | EXISTING/PROPOSED clearly stated |
| `external_view` | No | Must be external view, not section |
| `materials` | No | Materials indicated |
| `windows_doors` | No | Openings clearly depicted |
| `building_form` | No | Overall shape and massing shown |
| `ground_line` | No | Relationship to ground level |

#### SectionValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Valid scale (1:50, 1:100, 1:200, 1:500) with bar |
| `state_labelling` | Yes | EXISTING/PROPOSED consistently labelled |
| `cut_indicators` | No | Clear cut-through view |
| `floor_levels` | No | Floor levels and heights indicated |
| `site_levels` | No | Ground/site levels indicated |
| `neighbouring_relationship` | No | Adjacent structures shown |
| `site_identification` | No | Address or site description |

#### RoofPlanValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `scale` | Yes | Must be 1:50 or 1:100 with scale bar |
| `state_labelling` | Yes | EXISTING/PROPOSED clearly labelled |
| `north_arrow` | Yes | North arrow always required |
| `roof_features` | No | Roof features from above |
| `roof_geometry` | No | Ridges, hips, valleys shown |
| `roof_windows` | No | Rooflights, dormers indicated |
| `materials` | No | Roof covering materials |
| `dimensions` | No | Dimensions and ridge heights |
| `site_identification` | No | Address or site description |

#### DetailDrawingValidationChecks

| Check | Critical | Description |
|-------|----------|-------------|
| `state_labelling` | Yes | EXISTING/PROPOSED explicitly labelled |
| `scale` | No | 1:5, 1:10, or 1:20 (or 1:1/1:2 for joinery) |
| `component_detail` | No | Component/junction detail shown |
| `construction_information` | No | Construction method/materials |
| `dimensional_information` | No | Clear dimensioning |
| `drawing_clarity` | No | Clear title and identification |
| `site_identification` | No | Site identification if standalone |

---

## Validity Assessment

The overall validity assessment follows these rules:

1. **VALID**: All critical checks pass (COMPLIANT or NOT_APPLICABLE)
2. **INVALID**: Any critical check fails (MISSING or incorrect)
3. **CLARIFICATION_NEEDED**: Critical checks are UNCLEAR

Non-critical checks inform quality but don't affect validity.

---

## Example Response

```json
{
  "document_id": "floor-plan-001",
  "document_type": "floor_plan",
  "validity": "VALID",
  "confidence": "HIGH",
  "reasoning": "Floor plan shows ground floor layout with all critical requirements met...",
  "requirements_checked": [
    {
      "requirement": "scale",
      "status": "PASS",
      "details": "Scale 1:100 with linear scale bar present"
    },
    {
      "requirement": "floor_level",
      "status": "PASS",
      "details": "Ground Floor clearly labelled"
    }
  ],
  "execution_time": 3.45,
  "success": true,
  "classification_confidence": "HIGH",
  "classification_reasoning": "Internal room layout with floor level marker..."
}
```
