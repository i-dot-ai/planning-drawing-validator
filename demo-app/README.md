# Demo Application

← [Back to Repository Root](../README.md)

Stateless demo app for validating planning drawings against UK planning requirements.

---

## Overview

The **demo-app** is a simple REST API with demo frontend for user-facing document validation. It is **stateless** and provides a demonstration of the validation capabilities:

- **Simple Request/Response** - Upload document, get validation result immediately
- **Containerised Deployment** - Easy to run with Docker Compose

---

## Quick Start

Get the demo app running in under 5 minutes:

### 1. Configure Environment

```bash
# Copy environment configuration
cp ../.env.example ../.env

# Edit ../.env and configure LiteLLM gateway
IAI_LITELLM_PROJECT_NAME=drawing-validator
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash  # Any LiteLLM-supported model
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com
IAI_LITELLM_API_KEY=your-api-key

# See Configuration section below for model options
```

### 2. Start with Docker Compose

```bash
# Start demo system (backend + frontend)
cd demo-app
docker-compose up -d
```

### 3. Access the Application

- **Frontend UI**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### 4. Verify It's Working

You should see:
- Frontend loads with document upload interface
- Backend API responds at `/health`
- API documentation accessible at `/docs`

---

## Architecture

The demo app is a minimal stack with two components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Demo System                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  React Frontend (Port 3001)                                 │
│  └─ Document upload interface, results display              │
│                                                             │
│  FastAPI Backend (Port 8001)                                │
│  └─ Stateless validation API (NO database, NO storage)      │
│      Uses: planning-drawing-validator package               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

The API provides three endpoints for document validation:

### 1. Health Check

```http
GET /health
```

Service availability and version information.

**Response:**
```json
{
  "status": "healthy",
  "service": "demo-validation-api",
  "version": "1.0.0"
}
```

### 2. Get Drawing Types

```http
GET /drawing-types
```

Retrieve supported drawing types and their requirements.

**Response:**
```json
{
  "drawing_types": [
    {
      "type": "SITE_PLAN",
      "display_name": "Site Plan",
      "typical_scales": ["1:200", "1:500"],
      "requirements": [
        "Property boundaries clearly marked",
        "North arrow present",
        "Scale indicated"
      ]
    }
  ]
}
```

**Supported drawing types:**
- Site Plans, Floor Plans, Elevations, Sections, Location Plans, Roof Plans, Detail Drawings

### 3. Validate Document

```http
POST /validate
```

Upload and validate a planning drawing.

**Request:**
- Content-Type: `multipart/form-data`
- Parameter: `file` (required)
- Formats: PDF, PNG, JPG, TIFF
- Max size: 10MB

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "document_type": "FLOOR_PLAN",
  "validity": "VALID",
  "confidence": "HIGH",
  "reasoning": "Floor plan contains all required elements: scale 1:100, floor level clearly marked, room labels present.",
  "requirements_checked": [
    {
      "requirement": "Scale indicated",
      "status": "PASS",
      "details": "Scale 1:100 clearly marked"
    }
  ],
  "execution_time": 2.34,
  "success": true
}
```

**Processing pipeline:**
1. File upload & validation
2. Image extraction (PDF to images or direct load)
3. AI classification (identify drawing type)
4. Requirement validation (type-specific checks)
5. Structured response with detailed feedback

---

## Usage Examples

### cURL

```bash
# Validate a document
curl -X POST "http://localhost:8001/validate" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/floor_plan.pdf"

# Get drawing types
curl "http://localhost:8001/drawing-types"
```

### Python

```python
import requests

# Validate a document
with open("floor_plan.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8001/validate",
        files={"file": f}
    )

result = response.json()
print(f"Validity: {result['validity']}")
print(f"Type: {result['document_type']}")
print(f"Reasoning: {result['reasoning']}")
```

### JavaScript

```javascript
// Validate a document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8001/validate', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log('Valid:', result.validity);
console.log('Type:', result.document_type);
```

---

## Configuration

Configuration uses environment variables from repository root `.env` file.

### LiteLLM Gateway Configuration

The demo app uses **LiteLLM** for model-agnostic access to any Vision LLM provider (OpenAI, Anthropic, Google, Azure, etc.):

```bash
# Project name for tracking
IAI_LITELLM_PROJECT_NAME=drawing-validator

# Model to use (format: provider/model-name)
IAI_LITELLM_CHAT_MODEL=gemini/gemini-2.5-flash

# LiteLLM gateway URL
IAI_LITELLM_API_BASE=https://your-litellm-gateway.example.com

# API key for gateway authentication
IAI_LITELLM_API_KEY=your-api-key
```

**Supported model examples:**
- `gemini/gemini-2.5-flash` - Google Gemini
- `openai/gpt-4o` - OpenAI GPT-4o
- `anthropic/claude-sonnet-4-20250514` - Anthropic Claude

See [`.env.example`](../.env.example) for complete configuration options.

### Optional: Server Settings

```bash
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO
```

### Optional: LLM Observability

Enable tracing with [Langfuse](https://langfuse.com) (integrated with LiteLLM gateway):

```bash
IAI_LITELLM_LANGFUSE_PUBLIC_KEY=pk-lf-...
IAI_LITELLM_LANGFUSE_SECRET_KEY=sk-lf-...
IAI_LITELLM_LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Development

### Running Locally (without Docker)

**Backend:**

```bash
# Install dependencies
cd demo-app
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Set up environment
cp ../.env.example ../.env
# Edit ../.env with your configuration

# Run backend
cd backend
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**

```bash
# Install dependencies
cd demo-app/frontend
npm install

# Configure API endpoint (if needed)
# Edit .env or .env.local to set REACT_APP_API_URL

# Run frontend
npm start
```

Access:
- Frontend: http://localhost:3000 (dev server) or http://localhost:3001 (production build)
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Project Structure

```
demo-app/
├── backend/
│   ├── api.py              # FastAPI application with endpoints
│   ├── config.py           # Configuration management
│   └── schemas.py          # Pydantic response models
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── types.ts        # TypeScript types
│   └── Dockerfile
├── docker-compose.yml      # Container orchestration
├── Dockerfile              # Backend container image
├── pyproject.toml          # Python dependencies
└── README.md               # This file
```

## Related Documentation

- **[Repository Root README](../README.md)** - Project overview and architecture
- **[Planning Drawing Validator](../planning-drawing-validator/)** - Core validation package
- **[Evaluation App](../evaluation-app/)** - Stateful evaluation system with database
- **[Environment Configuration](../.env.example)** - Complete configuration reference
