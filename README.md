# Planning Drawing Validator

> AI-powered validation of UK planning application drawings using Vision Language Models

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

## What is this?

Planning Drawing Validator automatically classifies and validates planning application drawings (floor plans, elevations, site plans, etc.) against UK planning requirements using Vision Language Models. It uses [LiteLLM](https://docs.litellm.ai/) for model-agnostic access to any VLM provider (OpenAI, Anthropic, Google, Azure, etc.).

**Key Features:**
- **Automatic Classification** - Identifies drawing types (floor plan, elevation, section, etc.)
- **Requirement Validation** - Checks compliance with UK planning standards
- **Model Agnostic** - Works with any Vision LLM via LiteLLM (OpenAI, Anthropic, Google, Azure, etc.)
- **Configurable Reasoning Effort** - Control model thinking depth for cost/quality trade-offs
- **Transparent AI Reasoning** - Extended thinking mode shows validation logic (where supported)
- **Environmental Tracking** - Carbon impact metrics for LLM inference
- **Multiple Deployment Options** - CLI, REST API, or Python library

**Use Cases:**
- Pre-submission validation for planning applicants
- Initial triage for planning officers
- Quality assurance for architectural practices
- Training data generation for ML research

## Quick Start

### 5-Minute Demo with Docker

```bash
# Clone repository
git clone https://github.com/i-dot-ai/planning-drawing-validator.git
cd planning-drawing-validator

# Set up credentials
cp .env.example .env
# Edit .env and add your LiteLLM gateway API key

# Start demo application
cd demo-app
docker-compose up -d

# Access at http://localhost:3001
```

Upload a planning drawing and get instant validation results!

### Python Library Usage

```python
from planning_drawing_validator import DocumentValidator, Document

# Initialise validator
validator = DocumentValidator()

# Validate a document
document = Document(
    document_id="example-001",
    filename="floor_plan.pdf",
    file_path="path/to/floor_plan.pdf"
)

result = await validator.validate(document)

# Check results
print(f"Document Type: {result.document_type}")  # "floor_plan"
print(f"Valid: {result.validity}")                # "VALID"
print(f"Confidence: {result.confidence}")        # "HIGH"
print(f"Reasoning: {result.reasoning}")

# Review specific requirements
for req in result.requirements_checked:
    print(f"{req.requirement}: {req.status}")
    if req.details:
        print(f"  → {req.details}")
```

### CLI Usage

```bash
# Install core package
cd planning-drawing-validator
uv venv .venv && source .venv/bin/activate
uv pip install -e .

# Validate single document
validate-drawing floor_plan.pdf

# Batch validate directory
validate-drawing /path/to/drawings/ --output results.json

# See all options
validate-drawing --help
```

## Repository Structure

This is a **monorepo** containing three packages:

### 1. [planning-drawing-validator](./planning-drawing-validator/) - Core Package

**Installable Python library** for document validation.

- LLM-powered classification and validation
- CLI tool for batch processing
- Extensible storage abstraction (local, S3, Azure)
- [Full documentation](./planning-drawing-validator/README.md)

### 2. [demo-app](./demo-app/) - Demo Application

**Simple stateless demonstration** of the validator.

- REST API with OpenAPI/Swagger docs
- React frontend with drag-and-drop upload
- Docker Compose setup
- Quick start for testing and demos
- [Documentation](./demo-app/README.md)

### 3. [evaluation-app](./evaluation-app/) - Evaluation System

**Performance evaluation and quality assurance** platform.

- Ground truth management
- Accuracy metrics (precision, recall, F1)
- Multi-model comparison via `models.yaml` configuration
- Configurable reasoning effort per model
- Run history and comparison
- PostgreSQL database for results persistence
- **Internal QA use only** - not for production
- [Documentation](./evaluation-app/README.md)

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Client Application                         │
│              (CLI / REST API / Python Library)                 │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                   DocumentValidator                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Classification Stage                                 │  │
│  │     → Identify document type                             │  │
│  │     → Detect mixed plans                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│                             ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. Validation Stage                                     │  │
│  │     → Type-specific requirement checks                   │  │
│  │     → Concurrent validation for mixed plans              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌─────────────┐  ┌──────────┐
     │ LLM Client │  │   Storage   │  │ Prompts  │
     │ (LiteLLM)  │  │ (File/S3/   │  │          │
     │            │  │  Azure)     │  │          │
     └────────────┘  └─────────────┘  └──────────┘
```

**Key Design Principles:**
- **Model Agnostic** - Use any VLM provider via LiteLLM (switch models without code changes)
- **Storage Abstraction** - Swap local files for S3/Azure without code changes
- **Stateless Validation** - No database required for core functionality
- **Concurrent Processing** - Parallel validation for mixed plan documents

## Supported Drawing Types

| Type | Description | Typical Scale | Key Requirements |
|------|-------------|---------------|------------------|
| **Site Plan** | Property context | 1:200, 1:500 | Boundaries, north arrow, scale, access |
| **Floor Plan** | Building layout | 1:50, 1:100 | Room labels, dimensions, floor level |
| **Elevation** | External views | 1:50, 1:100 | All elevations, materials, heights |
| **Section** | Vertical cuts | 1:50, 1:100 | Floor heights, roof structure, ground levels |
| **Location Plan** | Site location | 1:1250, 1:2500 | Red line boundary, OS map base |
| **Roof Plan** | Roof layout | 1:50, 1:100 | Ridge heights, materials, drainage |
| **Detail Drawing** | Construction details | 1:5, 1:10, 1:20 | Materials, dimensions, assembly |
| **Mixed Plans** | Multiple drawings | Various | Validates each constituent |

## Configuration

All applications use environment variables. Create a `.env` file from the template:

```bash
cp .env.example .env
```

**Minimum Configuration:**

```bash
# LiteLLM Gateway Configuration (model-agnostic)
IAI_LITELLM_PROJECT_NAME=drawing-validator
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash  # Or any LiteLLM-supported model
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com
IAI_LITELLM_API_KEY=your-api-key

# Optional: Langfuse Tracing
IAI_LITELLM_LANGFUSE_PUBLIC_KEY=pk-lf-...
IAI_LITELLM_LANGFUSE_SECRET_KEY=sk-lf-...
IAI_LITELLM_LANGFUSE_HOST=https://cloud.langfuse.com
```

**Supported models** (any LiteLLM-compatible Vision LLM):
- `gemini/gemini-2.5-flash`, `gemini/gemini-2.5-pro`
- `openai/gpt-4o`, `openai/gpt-4o-mini`
- `anthropic/claude-sonnet-4-20250514`
- See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for full provider list

**Advanced Options:**

```bash
# Evaluation system (PostgreSQL required)
DATABASE_URL=postgresql://user:pass@localhost:5432/planning_validation  # pragma: allowlist secret

# Performance tuning
MAX_CONCURRENT_VALIDATIONS=5

# Storage backend (default: local filesystem)
STORAGE_BACKEND=s3  # or 'azure', 'gcs'
S3_BUCKET=planning-documents
```

See [.env.example](./.env.example) for complete configuration documentation.

## Development

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** (for frontend)
- **Docker & Docker Compose** (optional, for containerised setup)
- **UV** - Fast Python package manager (recommended)

### Setup Development Environment

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/i-dot-ai/planning-drawing-validator.git
cd planning-drawing-validator

# Set up pre-commit hooks
uv venv .venv
source .venv/bin/activate
uv pip install pre-commit
pre-commit install

# Install development dependencies
cd planning-drawing-validator
uv pip install -e ".[dev]"
```

### Code Quality

We maintain high code quality standards:

```bash
# Format and lint
ruff format .          # Format code
ruff check .           # Lint code

# Type checking
mypy .

# Security scanning
bandit -r src/
detect-secrets scan
```

**Quality Requirements:**
- Type hints on all public APIs
- Google-style docstrings
- No secrets or credentials in code
- Ruff formatting and linting passes
- Security scanning passes

## Deployment

### Docker (Recommended)

Each application has its own `docker-compose.yml`:

```bash
# Demo application (no database)
cd demo-app
docker-compose up -d

# Evaluation system (includes PostgreSQL)
cd evaluation-app
docker-compose up -d
docker-compose exec backend-evaluation alembic upgrade head
```

### Manual Deployment

See the README for each component:
- [Core Package](./planning-drawing-validator/README.md)
- [Demo App](./demo-app/README.md)
- [Evaluation System](./evaluation-app/README.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:

- Development setup instructions
- Code style guidelines
- Pull request process

**Quick Links:**
- [Security Policy](SECURITY.md)
- [Issue Templates](.github/ISSUE_TEMPLATE/)

## Community & Support

- **Bug Reports**: [GitHub Issues](https://github.com/i-dot-ai/planning-drawing-validator/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/i-dot-ai/planning-drawing-validator/discussions)
- **Security Issues**: See [SECURITY.md](SECURITY.md)
- **General Questions**: [GitHub Discussions](https://github.com/i-dot-ai/planning-drawing-validator/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this project in your research or work, please cite:

```bibtex
@software{planning_drawing_validator,
  title = {Planning Drawing Validator},
  author = {{UK Government Incubator for AI}},
  year = {2025},
  url = {https://github.com/i-dot-ai/planning-drawing-validator},
  license = {MIT}
}
```

---

**Developed by the UK Government Incubator for AI**
