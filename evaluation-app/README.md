# Evaluation Application

← [Back to Repository Root](../README.md)

Performance evaluation and quality assurance platform for the Planning Drawing Validator.

## Overview

The **evaluation-app** is an internal QA system for measuring validation accuracy against ground truth datasets. It provides comprehensive metrics, run comparison, and model evaluation capabilities.

**Key Features:**
- Ground truth management (Excel, JSON, YAML uploads)
- Accuracy metrics (precision, recall, F1 scores)
- Confusion matrix visualisation
- Run history and comparison
- Real-time progress tracking via WebSocket
- Multi-model evaluation support
- Export results with full statistics

**Note:** This is an internal QA tool, not intended for production deployment.

## Quick Start

### 1. Configure Environment

```bash
# Copy environment configuration
cp ../.env.example ../.env

# Edit ../.env with your LiteLLM gateway credentials
IAI_LITELLM_PROJECT_NAME=drawing-validator
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash  # Any LiteLLM-supported model
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com
IAI_LITELLM_API_KEY=your-api-key
```

### 2. Start with Docker Compose

```bash
cd evaluation-app
docker-compose up -d

# Run database migrations
docker-compose exec backend-evaluation alembic upgrade head
```

### 3. Access the Application

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Evaluation dashboard |
| Backend API | http://localhost:8000 | FastAPI orchestrator |
| API Docs | http://localhost:8000/docs | OpenAPI documentation |
| MinIO Console | http://localhost:9001 | Document storage admin |

## Architecture

```
evaluation-app/
├── backend/
│   ├── api/
│   │   ├── routers/          # API endpoints
│   │   │   ├── documents.py  # Document upload/retrieval
│   │   │   ├── evaluation.py # Evaluation orchestration
│   │   │   ├── ground_truth.py # Label management
│   │   │   └── runs.py       # Run history
│   │   ├── models/           # Response schemas
│   │   └── dependencies.py   # Dependency injection
│   ├── services/             # Business logic
│   ├── database/             # SQLAlchemy models
│   └── storage/              # S3/MinIO client
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # Page components
│   │   └── services/         # API client
│   └── package.json
├── alembic/                  # Database migrations
├── docker-compose.yml        # Service orchestration
└── README.md                 # This file
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| frontend-evaluation | 3000 | React dashboard |
| backend-evaluation | 8000 | FastAPI evaluation orchestrator |
| postgres | 5432 | Run history, ground truth, metrics |
| minio | 9000/9001 | S3-compatible document storage |

## Features

### Ground Truth Management

Upload ground truth labels in multiple formats:
- **Excel** (.xlsx, .xls) - Columns: filename, expected_validity
- **JSON** - Array of {filename, expected_validity}
- **YAML** - List format with filename and validity

### Evaluation Workflow

1. **Upload Documents** - Drag and drop PDF/image files
2. **Upload Ground Truth** - Match filenames to expected results
3. **Run Evaluation** - Execute validation pipeline
4. **View Results** - Accuracy metrics, confusion matrix, per-document details
5. **Export** - Download results with full statistics

### Metrics Tracked

- **Accuracy**: Overall correctness
- **Precision/Recall/F1**: Per-class metrics
- **Confusion Matrix**: VALID vs INVALID breakdown
- **Timing**: Total and per-document execution time
- **Environmental**: Energy and CO₂ via ecologits

## Development

### Running Locally

**Backend:**
```bash
cd evaluation-app
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Start backend
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd evaluation-app/frontend
npm install
npm start
```

### Database Migrations

```bash
# Create new migration
docker-compose exec backend-evaluation alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend-evaluation alembic upgrade head

# Rollback
docker-compose exec backend-evaluation alembic downgrade -1
```

### Logs and Debugging

```bash
# View backend logs
docker-compose logs -f backend-evaluation

# View frontend logs
docker-compose logs -f frontend-evaluation

# Restart services
docker-compose restart backend-evaluation frontend-evaluation
```

## Configuration

### Environment Variables

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/evaluation

# Storage (MinIO/S3)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=localhost:9000
MINIO_BUCKET=evaluation-documents

# LiteLLM Gateway (model-agnostic - supports any VLM provider)
IAI_LITELLM_PROJECT_NAME=drawing-validator
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com
IAI_LITELLM_API_KEY=your-api-key
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash
```

### Model Configuration

The evaluation app supports comparing multiple models via a YAML configuration file. This file is **not committed to git** (similar to `.env`), allowing each deployment to configure its own model list.

**Setup:**
```bash
# Copy the example configuration
cp backend/models.yaml.example backend/models.yaml

# Edit models.yaml with your available models
```

**Configuration format:**
```yaml
default_model: gemini/gemini-2.5-flash

models:
  - id: gemini/gemini-2.5-flash      # LiteLLM model identifier
    display_name: Gemini 2.5 Flash   # Shown in UI dropdown
    provider: Google                  # Optional: provider name
    reasoning_effort: low             # Optional: none, low, medium, high

  - id: litellm_proxy/gpt-4o         # Azure-hosted via LiteLLM proxy
    display_name: GPT-4o
    provider: OpenAI
    convert_pdf_to_images: true       # Required for Azure-hosted PDF support

  - id: anthropic/claude-sonnet-4-20250514
    display_name: Claude Sonnet 4
    provider: Anthropic
```

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Model identifier for LiteLLM (format: `provider/model-name`) |
| `display_name` | Yes | Human-readable name shown in the UI |
| `provider` | No | Provider name for grouping/display |
| `reasoning_effort` | No | Thinking depth: `none`, `low`, `medium`, `high` (model-dependent) |
| `supports_reasoning` | No | Whether model supports `reasoning_effort` param (default: `true`). Set to `false` for models that error with reasoning params (e.g., `gpt-4o-mini`) |
| `convert_pdf_to_images` | No | Convert PDFs to images before sending to LLM (required for Azure-hosted OpenAI) |

**Notes:**
- The `reasoning_effort` parameter controls extended thinking where supported, enabling cost/quality trade-offs.
- Set `supports_reasoning: false` for models that don't support reasoning parameters (most GPT-4 variants, mini/nano models). If not specified, defaults to `true`.
- Set `convert_pdf_to_images: true` for Azure-hosted OpenAI models. The Azure Chat Completions API doesn't support the `file` content type for PDFs, so PDFs are converted to PNG images before being sent to the model.

**Model Performance:**

The validation prompts and Pydantic schemas were developed and tuned using Anthropic Claude models, so evaluation performance may be biased towards these models. In practice:

- **Anthropic models** (Claude 3.5/4 Sonnet, Haiku) — Best performance, as prompts were optimised for these
- **Google Gemini models** (Gemini 2.0/2.5 Flash) — Perform well, comparable results
- **OpenAI models** (GPT-4o, GPT-4.1) — Some drop-off in accuracy observed

For Azure-hosted OpenAI models, PDFs are converted to PNG images before being sent to the LLM. This is necessary because the Azure Chat Completions API doesn't support the `file` content type for PDFs, and the LiteLLM Responses API isn't available via the proxy. The image-based approach should not significantly impact model performance compared to native PDF handling.

## Related Documentation

- **[Repository Root README](../README.md)** - Project overview
- **[Planning Drawing Validator](../planning-drawing-validator/)** - Core validation package
- **[Demo App](../demo-app/)** - Stateless demo API
