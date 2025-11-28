# Planning Drawing Validator

← [Back to Repository Root](../README.md)

Core validation package for planning drawing validation using LLM-based document classification and validation.

## Overview

This is the **core validation package** - a standalone Python library that validates planning documents through a two-stage LLM pipeline. It has zero infrastructure dependencies and can be used independently of the evaluation or production applications.

**Pipeline:**
```
Document → Classification → Validation → Result
           (Document Type)   (Validity)
```

**Key Features:**
- Two-stage LLM validation (classification → validation)
- Support for multiple document types (site plans, floor plans, elevations, etc.)
- Mixed drawing validation (documents with multiple constituent drawings)
- Configurable concurrency for batch processing
- Local filesystem and cloud storage support
- Optional Langfuse tracing for LLM observability
- Clean Python API and CLI interface

## Quick Start

### Installation

```bash
cd planning-drawing-validator

# Create environment with UV
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[dev]"       # Development tools
uv pip install -e ".[langfuse]"  # LLM tracing
```

### Configuration

Set required environment variables for i-dot-ai-utilities LiteLLM integration:

```bash
# Required: LiteLLM configuration
export IAI_LITELLM_PROJECT_NAME="planning-validator"
export IAI_LITELLM_API_BASE="https://your-litellm-gateway.example.com"
export IAI_LITELLM_API_KEY="your-api-key"  # pragma: allowlist secret
export IAI_LITELLM_CHAT_MODEL="gemini/gemini-2.5-flash"  # Or any LiteLLM-supported model

# Optional: Langfuse tracing
export LANGFUSE_ENABLED="true"
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."  # pragma: allowlist secret
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

**Tip:** Create a `.env` file in the repository root (auto-loaded by the package):
```bash
cp ../.env.example ../.env
# Edit .env with your credentials
```

## Usage

### Command-Line Interface

```bash
# Validate single document
validate-drawing site-plan.pdf

# Validate directory
validate-drawing documents/

# Control concurrency
validate-drawing documents/ --concurrent 10

# Save results to JSON
validate-drawing documents/ --output results.json

# Enable verbose logging
validate-drawing site-plan.pdf --verbose
```

### Python API

**Single Document:**

```python
from planning_drawing_validator import DocumentValidator, Document
import asyncio

async def validate():
    validator = DocumentValidator(max_concurrent=5)

    document = Document(
        document_id="site-plan-001",
        filename="site-plan.pdf",
        file_path="/path/to/site-plan.pdf"
    )

    result = await validator.validate(document)

    # Classification results
    print(f"Type: {result.document_type}")
    print(f"Classification: {result.classification_confidence}")

    # Validation results
    print(f"Validity: {result.validity}")
    print(f"Confidence: {result.confidence}")
    print(f"Time: {result.execution_time:.2f}s")

    # Requirements checked
    for req in result.requirements_checked:
        print(f"  {req.requirement}: {req.status}")

asyncio.run(validate())
```

**Batch Processing:**

```python
from planning_drawing_validator import DocumentValidator, Document
import asyncio

async def validate_batch():
    validator = DocumentValidator(max_concurrent=10)

    documents = [
        Document(document_id="doc1", filename="plan1.pdf", file_path="/path/to/plan1.pdf"),
        Document(document_id="doc2", filename="plan2.pdf", file_path="/path/to/plan2.pdf"),
        Document(document_id="doc3", filename="plan3.pdf", file_path="/path/to/plan3.pdf"),
    ]

    # Validate concurrently
    results = await asyncio.gather(*[validator.validate(doc) for doc in documents])

    for result in results:
        print(f"{result.document_id}: {result.validity} ({result.document_type})")

asyncio.run(validate_batch())
```

**Cloud Storage:**

```python
from planning_drawing_validator import DocumentValidator, Document

# Validate document from cloud storage
document = Document(
    document_id="cloud-doc-001",
    filename="floor-plan.pdf",
    storage_key="planning-docs/floor-plan.pdf"  # Storage identifier
)

validator = DocumentValidator(
    storage_prefix="planning-docs/",  # Optional prefix
    max_concurrent=5
)

result = await validator.validate(document)
```

## Document Types Supported

| Document Type | Description | Key Requirements |
|--------------|-------------|------------------|
| `site_plan` | Property boundaries, access, parking | Scale 1:200/1:500, boundaries, north arrow |
| `floor_plan` | Building floor layouts | Room labels, scale 1:50/1:100, floor level |
| `elevation` | External building views | Face labelling, scale 1:50/1:100, materials |
| `section_drawing` | Cross-sectional views | Cut indicators, scale 1:50-1:500, floor levels |
| `roof_plan` | Roof layout and materials | Roof geometry, scale 1:50/1:100, north arrow |
| `location_plan` | Site context and surroundings | Scale 1:1250/1:2500, red line boundary, north arrow |
| `detail_drawing` | Construction details | Component detail, scale 1:5-1:20, dimensions |
| `mixed_plans` | Multiple drawing types in one | Validates each constituent separately |

## Architecture

### Package Structure

```
planning-drawing-validator/
├── src/planning_drawing_validator/
│   ├── __init__.py           # Public API exports
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration management
│   ├── models.py             # Core data models
│   ├── types.py              # Type aliases
│   ├── validator.py          # Main validation orchestration
│   ├── storage.py            # Storage abstraction (filesystem/cloud)
│   ├── exceptions.py         # Custom exceptions
│   ├── logging.py            # Logging configuration
│   │
│   ├── llm/                  # LLM client integration
│   │   ├── __init__.py
│   │   ├── protocol.py       # LLM protocol interface
│   │   ├── litellm_client.py # i-dot-ai-utilities LiteLLM implementation
│   │   └── factory.py        # LLM client factory
│   │
│   └── pipeline/             # Validation pipeline
│       ├── __init__.py
│       ├── runner.py         # Stage execution (classification + validation)
│       ├── schemas.py        # Pydantic schemas for all document types
│       └── prompts/          # LLM prompts
│           ├── classification.txt
│           └── validation.txt
│
├── pyproject.toml           # Package configuration
└── README.md                # This file
```

### Validation Pipeline

**Stage 1: Classification**
- Identify document type (site plan, floor plan, etc.)
- Detect mixed drawings with multiple constituent types
- Output: document type, confidence, reasoning

**Stage 2: Validation**
- Validate against type-specific requirements
- For mixed drawings: validate each constituent separately
- Output: validity, confidence, requirements checked

**Execution:**
- Stages run sequentially per document
- Multiple documents processed concurrently
- Configurable concurrency limits

### Data Models

**Document** (Input):
```python
@dataclass
class Document:
    document_id: str          # Unique identifier
    filename: str             # Original filename
    file_path: str | None     # Local file path (optional)
    storage_key: str | None   # Cloud storage identifier (optional)
```

**ValidationResult** (Output):
```python
@dataclass
class ValidationResult:
    document_id: str
    document_type: str                    # Classified type
    validity: str                         # VALID, INVALID, ERROR
    reasoning: str                        # LLM's detailed reasoning
    confidence: str                       # HIGH, MEDIUM, LOW
    requirements_checked: list[Requirement]
    execution_time: float                 # Seconds
    success: bool
    error_message: str | None
    is_mixed_drawing: bool
    constituent_drawings: list[IndividualDrawingResult] | None
    classification_confidence: str        # Classification stage confidence
    classification_reasoning: str         # Classification stage reasoning
```

## Development

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix issues
ruff check --fix .

# Type checking
mypy src/planning_drawing_validator
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Configuration

### Environment Variables

**Required:**
```bash
IAI_LITELLM_PROJECT_NAME=planning-validator     # Project identifier
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com  # LiteLLM gateway URL
IAI_LITELLM_API_KEY=your-api-key                # API key
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash  # Any LiteLLM-supported model
```

**Optional:**
```bash
# Concurrency (default: 10)
MAX_CONCURRENT=20

# Langfuse tracing
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Model Configuration

The package uses i-dot-ai-utilities' LiteLLM integration for model-agnostic access to any Vision LLM:
- Configure model via `IAI_LITELLM_CHAT_MODEL`
- Format: `provider/model-name` (e.g., `gemini/gemini-2.5-flash`, `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`)
- Supports any LiteLLM-compatible provider (OpenAI, Anthropic, Google, Azure, etc.)
- Configure reasoning effort where supported (none, low, medium, high)
- Automatically handles authentication and routing

## Related Documentation

- **[Repository Root README](../README.md)**: Overview of the entire monorepo
- **[Evaluation App](../evaluation-app/README.md)**: QA testing system with metrics
- **[Demo App](../demo-app/README.md)**: Stateless demo API

## License

MIT License - see [LICENSE](../LICENSE) file for details.
