# Validation Pipeline

## Overview

The validation pipeline processes planning documents through a 2-stage sequential process to determine document type and validity against UK planning requirements.

```
┌──────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐
│ Document │───>│  CLASSIFY  │───>│  VALIDATE  │───>│  Result  │
└──────────┘    └────────────┘    └────────────┘    └──────────┘
   (PDF/Image)   (Document Type)  (Validity Check)   (ValidationResult)
```

## Pipeline Structure

```
pipeline/
├── __init__.py           # Public API exports
├── runner.py             # StageRunner - orchestrates both stages
├── schemas.py            # Pydantic schemas for classification and validation
├── prompts/
│   ├── classification.txt  # Classification prompt
│   └── validation.txt      # Generic validation prompt
└── README.md             # This file
```

## Stage 1: Classification

**Purpose**: Identify the type of planning document

**Implementation**: `runner.py` (`run_classification` method)

**Input**:
- Document images (PDF converted to images or direct image upload)
- Filename hint (optional, may contain type clues)

**Process**:
1. Load classification prompt from `prompts/classification.txt`
2. Send document + prompt to LLM
3. LLM analyses visual content and text
4. Parse structured JSON response into `ClassificationResponse` schema

**Output**: `ClassificationResponse` (Pydantic model)
```python
ClassificationResponse(
    document_type="FLOOR_PLAN",      # DocumentType enum
    confidence="HIGH",                # Confidence enum: HIGH, MEDIUM, LOW
    reasoning="This shows a floor layout with room labels...",
    constituent_drawings=[            # For MIXED_PLANS only
        ConstituentDrawing(
            drawing_type="floor_plan",
            location_on_sheet="upper half",
            description="Ground floor layout"
        )
    ]
)
```

**Supported Document Types** (`DocumentType` enum in `schemas.py`):
- `FLOOR_PLAN`: Building floor layouts with room labels
- `ELEVATION`: External building views (front, rear, side)
- `SECTION_DRAWING`: Cross-sectional views showing internal structure
- `SITE_PLAN`: Property boundaries, access, parking
- `SITE_LOCATION_PLAN`: Site context and surroundings
- `ROOF_PLAN`: Roof layout and materials
- `DETAIL_DRAWING`: Construction details and junctions
- `MIXED_PLANS`: Multiple document types in one file
- `OTHER_PLANS`: General planning drawings not fitting other categories

## Stage 2: Validation

**Purpose**: Validate document against UK planning requirements

**Implementation**: `runner.py` (`run_validation` method)

**Input**:
- Document images
- Classification result from Stage 1
- Document type (from classification or override)

**Process**:
1. Determine validation checks based on document type
2. Load generic validation prompt from `prompts/validation.txt`
3. Select type-specific validation checks from `VALIDATION_CHECK_MODELS`
4. Create dynamic response model with `create_validation_response_model()`
5. Send document + prompt to LLM with response schema
6. Parse structured JSON response

**For Mixed Plans**: Validates each constituent drawing separately and aggregates results

**Output**: `ValidationResponse` (dynamically created Pydantic model)
```python
# For a floor plan
ValidationResponse(
    validity_assessment="VALID",     # "VALID" or "INVALID"
    overall_confidence="HIGH",       # Confidence enum
    assessment_reasoning="Floor plan contains all required elements...",
    validation_checks=FloorPlanValidationChecks(
        room_labels=ValidationCheck(
            status="COMPLIANT",
            evidence="All rooms clearly labelled: Kitchen, Lounge, Bedroom 1, etc."
        ),
        dimensions=ValidationCheck(
            status="COMPLIANT",
            evidence="Room dimensions shown in metres"
        ),
        scale=ValidationCheck(
            status="PRESENT",
            evidence="Scale 1:50 indicated"
        ),
        # ... more checks
    )
)
```

## Schemas (`schemas.py`)

### Classification Schemas

```python
class DocumentType(str, Enum):
    """Supported planning document types."""
    FLOOR_PLAN = "FLOOR_PLAN"
    ELEVATION = "ELEVATION"
    SECTION_DRAWING = "SECTION_DRAWING"
    SITE_PLAN = "SITE_PLAN"
    # ... more types

class Confidence(str, Enum):
    """Confidence levels for classification and validation."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ConstituentDrawing(BaseModel):
    """Individual drawing within a mixed_plans document."""
    drawing_type: str
    location_on_sheet: str
    description: str

class ClassificationResponse(BaseModel):
    """Classification result structure."""
    document_type: DocumentType
    confidence: Confidence
    reasoning: str
    constituent_drawings: list[ConstituentDrawing] | None = None
```

### Validation Schemas

```python
class ValidationCheck(BaseModel):
    """Individual requirement check result."""
    status: str  # COMPLIANT, PRESENT, MISSING, UNCLEAR, NOT_APPLICABLE
    evidence: str  # Specific observable details

class FloorPlanValidationChecks(BaseModel):
    """Floor plan-specific validation requirements."""
    room_labels: ValidationCheck
    dimensions: ValidationCheck
    scale: ValidationCheck
    walls_and_openings: ValidationCheck
    floor_level: ValidationCheck
    north_arrow: ValidationCheck

# Similar models for each document type:
# - ElevationValidationChecks
# - SectionDrawingValidationChecks
# - SitePlanValidationChecks
# - etc.

# Mapping of document types to validation check models
VALIDATION_CHECK_MODELS: dict[str, type[BaseModel]] = {
    "FLOOR_PLAN": FloorPlanValidationChecks,
    "ELEVATION": ElevationValidationChecks,
    "SECTION_DRAWING": SectionDrawingValidationChecks,
    # ...
}

def create_validation_response_model(
    validation_checks_model: type[BaseModel]
) -> type[BaseModel]:
    """
    Dynamically create a ValidationResponse model with type-specific checks.

    Returns a Pydantic model with structure:
    - validity_assessment: str
    - overall_confidence: Confidence
    - assessment_reasoning: str
    - validation_checks: <document_type>ValidationChecks
    """
```

## Usage

### Using StageRunner Directly

```python
from planning_drawing_validator.pipeline import StageRunner
from planning_drawing_validator.llm import create_llm_client

# Create LLM client
llm_client = create_llm_client()

# Create stage runner
runner = StageRunner(llm_client=llm_client)

# Stage 1: Classify document
classification = await runner.run_classification(
    document_part=document_bytes,  # PDF bytes or image bytes
    filename="floor_plan.pdf"      # Optional hint
)

print(f"Type: {classification.document_type}")
print(f"Confidence: {classification.confidence}")
print(f"Reasoning: {classification.reasoning}")

# Stage 2: Validate document
validation, carbon_impact, thinking = await runner.run_validation(
    document_part=document_bytes,
    document_type=classification.document_type,
    constituent_drawings=classification.constituent_drawings  # For mixed plans
)

print(f"Valid: {validation.validity_assessment}")
print(f"Confidence: {validation.overall_confidence}")
print(f"Reasoning: {validation.assessment_reasoning}")

# Check specific requirements
for field_name, check in validation.validation_checks:
    print(f"{field_name}: {check.status} - {check.evidence}")
```

### Using DocumentValidator (Recommended)

```python
from planning_drawing_validator import DocumentValidator, Document

# High-level API handles both stages automatically
validator = DocumentValidator()

document = Document(
    document_id="doc_001",
    filename="floor_plan.pdf",
    file_path="/path/to/floor_plan.pdf"
)

result = await validator.validate(document)

# Result includes both classification and validation
print(f"Type: {result.document_type}")
print(f"Valid: {result.validity}")
print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning}")
```

## Data Flow

```python
# Complete pipeline flow

# Input: Document bytes
document_bytes = Path("floor_plan.pdf").read_bytes()

# Stage 1: Classification
classification = await runner.run_classification(
    document_part=document_bytes,
    filename="floor_plan.pdf"
)
# → ClassificationResponse(document_type="FLOOR_PLAN", confidence="HIGH", ...)

# Stage 2: Validation (with classification result)
validation, carbon, thinking = await runner.run_validation(
    document_part=document_bytes,
    document_type=classification.document_type
)
# → ValidationResponse(
#     validity_assessment="VALID",
#     validation_checks=FloorPlanValidationChecks(...)
#   )

# Output: Combined result
# Both classification and validation data available
```

## Prompts

### Classification Prompt (`prompts/classification.txt`)

**Purpose**: Teach LLM to identify planning document types

**Contents**:
- List of allowed document types
- Key visual discriminators for each type
- Example characteristics
- Instructions for handling mixed plans
- JSON response format specification

**Schema Binding**: Prompt instructs LLM to return JSON matching `ClassificationResponse` schema

### Validation Prompt (`prompts/validation.txt`)

**Purpose**: Generic validation framework for all document types

**Contents**:
- UK planning requirements overview
- Generic validation approach
- Instructions for assessing compliance
- JSON response format specification

**Schema Binding**:
- Prompt is generic and works for all document types
- Type-specific validation checks come from Pydantic schemas
- `create_validation_response_model()` dynamically combines them

**Example**:
```python
# For floor plan
validation_checks_model = VALIDATION_CHECK_MODELS["FLOOR_PLAN"]
# → FloorPlanValidationChecks

response_model = create_validation_response_model(validation_checks_model)
# → ValidationResponse with FloorPlanValidationChecks

# LLM receives JSON schema from response_model
schema = response_model.model_json_schema()
# → Includes all FloorPlanValidationChecks fields

# LLM returns JSON matching this schema
result = await llm.generate_structured_output(
    messages=[prompt, document],
    response_model=response_model
)
```

## Mixed Plans Handling

When a document contains multiple drawing types (e.g., floor plan + elevations on one sheet):

**Classification Stage**:
```python
classification = ClassificationResponse(
    document_type="MIXED_PLANS",
    confidence="HIGH",
    reasoning="Document contains multiple drawing types",
    constituent_drawings=[
        ConstituentDrawing(
            drawing_type="floor_plan",
            location_on_sheet="upper section",
            description="Ground floor layout"
        ),
        ConstituentDrawing(
            drawing_type="elevation",
            location_on_sheet="lower section",
            description="Front elevation"
        )
    ]
)
```

**Validation Stage**:
```python
# Validates each constituent separately
validation = await runner.run_validation(
    document_part=document_bytes,
    document_type="MIXED_PLANS",
    constituent_drawings=classification.constituent_drawings
)

# Returns aggregated validation with constituent-specific checks
# Uses _validate_mixed_plans() internal method
```

## Error Handling

### Classification Errors

```python
try:
    classification = await runner.run_classification(...)
except Exception as e:
    # LLM call failed, parsing failed, etc.
    # Caller should handle by returning error result
    logger.error(f"Classification failed: {e}")
```

### Validation Errors

```python
try:
    validation, carbon, thinking = await runner.run_validation(...)
except Exception as e:
    # LLM call failed, schema validation failed, etc.
    # Caller should handle by returning error result
    logger.error(f"Validation failed: {e}")
```

### Best Practices

- Don't let one document error stop batch processing
- Log detailed error information for debugging
- Return structured error results to callers
- Include error context (document ID, filename, stage)

## Performance

### Timing Characteristics

- **Classification**: 2-5 seconds per document
- **Validation**: 3-8 seconds per document
- **Total**: 5-13 seconds per document (sequential stages)

### Concurrency

The pipeline itself runs stages **sequentially** per document:
1. Classification must complete before validation
2. Validation needs classification result

However, `DocumentValidator` processes **multiple documents in parallel**:
```python
validator = DocumentValidator(max_concurrent=10)  # 10 documents at once

# Each document runs both stages sequentially
# But 10 documents are processed concurrently
```

### Optimization Tips

1. **Batch Processing**: Process multiple documents concurrently
2. **Prompt Caching**: LLM providers may cache repeated prompts
3. **Document Encoding**: Encode documents efficiently (base64 for images)
4. **Async/Await**: Use async operations throughout

## Extending the Pipeline

### Adding a New Document Type

**Step 1**: Update classification prompt (`prompts/classification.txt`)
```txt
Add to allowed categories:
- new_document_type: Description of the new type

Add to key discriminators section:
- Visual characteristics
- Typical title cues
- Example features
```

**Step 2**: Create validation checks in `schemas.py`
```python
class NewDocumentTypeValidationChecks(BaseModel):
    """Validation checks for new document type."""
    required_element_1: ValidationCheck = Field(
        description="Check for required element 1"
    )
    required_element_2: ValidationCheck = Field(
        description="Check for required element 2"
    )
    # ... more checks

# Add to VALIDATION_CHECK_MODELS
VALIDATION_CHECK_MODELS["NEW_DOCUMENT_TYPE"] = NewDocumentTypeValidationChecks
```

**Step 3**: Add to `DocumentType` enum
```python
class DocumentType(str, Enum):
    # ... existing types
    NEW_DOCUMENT_TYPE = "NEW_DOCUMENT_TYPE"
```

The generic validation prompt (`prompts/validation.txt`) automatically works with the new type - no changes needed.

## Common Issues

**Issue**: Classification always returns low confidence
- **Check**: Prompt file loaded correctly (`prompts/classification.txt`)
- **Check**: LLM has vision capability enabled
- **Check**: Document encoding is correct (base64 for images)

**Issue**: Validation schema mismatch errors
- **Check**: Document type exists in `VALIDATION_CHECK_MODELS`
- **Check**: Pydantic model fields match prompt expectations
- **Check**: LLM response parsing succeeds

**Issue**: Mixed plans not validating constituents
- **Check**: Classification returns `constituent_drawings` list
- **Check**: `_validate_mixed_plans()` is called
- **Check**: Each constituent type exists in `VALIDATION_CHECK_MODELS`

**Issue**: Slow performance
- **Check**: LLM latency (this is the main bottleneck)
- **Check**: Concurrency settings in `DocumentValidator`
- **Check**: Document size (large PDFs take longer)

## Further Reading

- [Main Package README](../../../README.md) - Overall architecture and quick start
- [Examples](../../../examples/) - Usage examples with code
- [Validator Documentation](../validator.py) - High-level API
- [LLM Integration](../llm/) - LLM client implementation
