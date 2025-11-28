# Evaluation System Frontend

**This frontend is for the EVALUATION SYSTEM only** - it provides QA testing and performance analysis capabilities for the document validation system.

## Purpose

This is an internal tool for:
- Running evaluation experiments against ground truth datasets
- Managing ground truth data
- Viewing performance metrics and confusion matrices
- Testing prompt versions
- Analysing run history and results

**This is NOT the production frontend** - there is no production frontend as the production system is a stateless API-only service.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Evaluation System Frontend              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  View Modes:                                         │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐           │
│  │   Run   │  │ History  │  │ Prompts  │           │
│  │  Mode   │  │   View   │  │   View   │           │
│  └─────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  Features:                                           │
│  • Start/stop evaluation runs                       │
│  • Upload test documents                            │
│  • Define ground truth expectations                 │
│  • View live metrics (accuracy, precision, recall)  │
│  • Browse run history                               │
│  • Manage prompt versions                           │
│  • Compare results                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
         │                                   ▲
         │ API Calls                         │ WebSocket
         ▼                                   │ Updates
┌────────────────────────────────────────────┴─────────┐
│         Backend (review.evaluation.web_server)       │
│                   Port 8000                          │
└──────────────────────────────────────────────────────┘
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible component primitives
- **Lucide Icons** - Icon library
- **Sonner** - Toast notifications
- **React Markdown** - Markdown rendering

## Development

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend evaluation server running on port 8000

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# Runs on http://localhost:3000
# Proxies API requests to http://localhost:8000 (backend)
```

### Build

```bash
# Production build
npm run build

# Output in build/ directory
# Static files served by backend at http://localhost:8000
```

### Docker

This frontend is part of the evaluation Docker Compose setup:

```bash
# From the evaluation-app directory
# Start evaluation system (includes frontend)
docker-compose up -d

# Access at http://localhost:3000
```

## Project Structure

```
src/
├── components/          # React components
│   ├── ui/             # Reusable UI components (shadcn/ui)
│   ├── chat/           # Chat interface components
│   ├── DocumentCard.tsx
│   ├── DocumentQueue.tsx
│   ├── LiveMetrics.tsx
│   ├── HistoryView.tsx
│   ├── PromptsView.tsx
│   ├── RunConfigModal.tsx
│   └── ...
├── contexts/           # React contexts
│   └── EvaluationContext.tsx
├── hooks/              # Custom React hooks
│   ├── useWebSocket.ts
│   └── useEvaluation.ts
├── types/              # TypeScript type definitions
├── App.tsx             # Main application component
└── index.tsx           # Application entry point
```

## Key Components

### Run Mode (Default View)

- **ControlPanel**: Start/stop evaluation runs, configure settings
- **LiveMetrics**: Real-time accuracy, precision, recall
- **DocumentQueue**: Queued/processing/completed documents
- **DocumentCard**: Individual document results with details

### History View

- **HistoryView**: Browse past evaluation runs
- **RunComparison**: Compare metrics across runs
- Filter by date, run ID, accuracy

### Prompts View

- **PromptsView**: Manage prompt versions
- **VersionTree**: Visualise prompt evolution
- Edit and test prompt changes

## API Integration

The frontend communicates with the backend through:

### REST API (Port 8000)

```typescript
// Start evaluation run
POST /api/start-evaluation
{
  "concurrency": 10,
  "maxSamples": 100,
  "documentIds": ["doc1", "doc2"]
}

// Get current run status
GET /api/current-run

// Stop evaluation
POST /api/stop-evaluation

// Get run history
GET /api/runs

// Upload documents
POST /api/upload
```

### WebSocket (Port 8000)

```typescript
// Real-time updates
ws://localhost:8000/ws

// Message types:
{
  "type": "evaluation_started",
  "run_id": "run_123",
  "total_documents": 100
}

{
  "type": "document_completed",
  "document_id": "doc1",
  "accuracy": 0.95
}

{
  "type": "evaluation_completed",
  "metrics": { ... }
}
```

## Environment Variables

```bash
# Backend API URL (configured in package.json proxy)
# Development: http://localhost:8000 (automatic proxy)
# Production: served from backend at same origin
```

## Deployment

### Development

```bash
npm start
# Runs on http://localhost:3000
# Proxies API to http://localhost:8000
```

### Production (via Backend)

The backend serves the built frontend:

```python
# review/evaluation/web_server.py
frontend_path = Path(__file__).parent.parent / "frontend" / "build"
app.mount("/static", StaticFiles(directory=frontend_path / "static"))

@app.get("/")
async def serve_frontend():
    return FileResponse(frontend_path / "index.html")
```

Access at: `http://localhost:8000/`

### Docker

The frontend is built and served in the evaluation Docker Compose setup:

```yaml
# evaluation-app/docker-compose.yml
frontend-evaluation:
  build:
    context: ./review/frontend
    dockerfile: Dockerfile
  ports:
    - "3000:3000"
```

Built with nginx multi-stage build for production-optimised serving.

## Features

### Evaluation Management
- Configure and start evaluation runs
- Set concurrency, max samples, document filters
- Stop running evaluations
- View real-time progress

### Metrics Dashboard
- Live accuracy, precision, recall
- Confusion matrix (TP, TN, FP, FN)
- Document-level results
- Aggregated statistics

### Ground Truth Management
- Upload ground truth datasets (JSON/YAML/Excel)
- Define expected validity per document
- View and edit ground truth data
- Validate ground truth schemas

### Run History
- Browse past evaluation runs
- Filter by date, accuracy, status
- Compare metrics across runs
- Download results (JSON)

### Prompt Version Control
- View prompt versions
- Edit and test prompts
- Track prompt performance
- Rollback to previous versions

## Development Guidelines

### Code Style

- **TypeScript**: Strict mode enabled
- **React**: Functional components with hooks
- **Async**: Use async/await, not promises
- **Error Handling**: Toast notifications for errors

### Component Structure

```typescript
import React from 'react';

interface Props {
  // Props interface
}

export const Component: React.FC<Props> = ({ prop1, prop2 }) => {
  // Hooks at top
  const [state, setState] = useState();

  // Event handlers
  const handleClick = () => {};

  // Render
  return <div>...</div>;
};
```

### API Calls

Use async/await with proper error handling:

```typescript
const startEvaluation = async () => {
  try {
    const response = await fetch('/api/start-evaluation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error(`Failed: ${response.statusText}`);
    }

    const data = await response.json();
    toast.success('Evaluation started');
    return data;
  } catch (error) {
    toast.error(`Error: ${error.message}`);
    throw error;
  }
};
```

## Code Quality

```bash
# Lint
npm run lint

# Format code
npm run format
```

## Troubleshooting

### Backend Connection Issues

**Error**: `Failed to fetch` or `CORS error`

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check proxy setting in package.json
"proxy": "http://localhost:8000"

# Restart dev server
npm start
```

### WebSocket Not Connecting

**Error**: WebSocket connection failed

**Solution**:
```bash
# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws

# Check nginx proxy settings (if using Docker)
# Ensure WebSocket upgrade headers are set
```

### Build Fails

**Error**: Build fails with TypeScript errors

**Solution**:
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Check TypeScript version compatibility
npm list typescript

# Fix type errors
npm run lint:fix
```

## Location

This frontend is located at `review/evaluation/frontend/` to clearly indicate it's part of the evaluation system, not the production backend.

```
review/
├── backend/                # Production validation code
│   ├── validator.py
│   └── production_api.py
└── evaluation/             # Evaluation system (QA tool)
    ├── web_server.py
    ├── evaluator.py
    └── frontend/           # ← This frontend (evaluation UI)
        ├── src/
        └── public/
```

## Related Documentation

- [Main README](../../../README.md) - Project overview
- [DOCKER_SETUP.md](../../../DOCKER_SETUP.md) - Docker configuration guide
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - System architecture
- [Evaluation Web Server](../web_server.py) - Backend that serves this frontend

## Notes

- This frontend is **not used in production** - the production system is API-only
- All features are designed for **internal QA and testing**
- Not optimised for public-facing use (no authentication, rate limiting, etc.)
- Designed to run on internal networks only
