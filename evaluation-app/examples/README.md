# Evaluation App - Examples

Examples demonstrating how to use the evaluation app programmatically and via API.

## Prerequisites

1. **Install the evaluation app**:
   ```bash
   cd evaluation-app
   pip install -e .
   ```

2. **Set up database**:
   ```bash
   # Option 1: PostgreSQL (recommended for production)
   export DATABASE_URL="postgresql://user:password@localhost/planning_validator"  # pragma: allowlist secret

   # Option 2: SQLite (for development)
   export DATABASE_URL="sqlite:///./evaluation.db"

   # Run migrations
   alembic upgrade head
   ```

3. **Configure storage**:
   ```bash
   # Option 1: S3 (recommended for production)
   export STORAGE_TYPE="s3"
   export AWS_REGION="eu-west-2"
   export S3_BUCKET_NAME="planning-validator-evaluations"

   # Option 2: Local storage (for development)
   export STORAGE_TYPE="local"
   export LOCAL_STORAGE_PATH="./storage"
   ```

4. **Set API keys**:
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"  # pragma: allowlist secret
   ```

## Running Evaluations

### Via Web Interface

1. **Start the web server**:
   ```bash
   python backend/web_server.py
   ```

2. **Open browser** to `http://localhost:8000`

3. **Upload documents** and start evaluation via the UI

### Via API

See [`api_examples.md`](./api_examples.md) for detailed API usage.

Quick example:
```bash
# Start evaluation
curl -X POST http://localhost:8000/api/evaluation/start \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["doc1", "doc2"]}'
```

### Programmatically

See [`run_evaluation.py`](./run_evaluation.py) for a complete example.

```python
from backend.services.evaluator import evaluate_documents
from backend.config import Config

config = Config.load()
results = await evaluate_documents(
    document_ids=["doc1", "doc2"],
    config=config
)
```

## Managing Ground Truth

Ground truth labels are used to evaluate the accuracy of the validator.

### Ground Truth JSON Format

```json
[
  {
    "document_id": "doc_123",
    "filename": "site_plan.pdf",
    "expected_validity": true,
    "expected_document_type": "SITE_PLAN",
    "notes": "Clear site plan with all required elements"
  },
  {
    "document_id": "doc_124",
    "filename": "invalid_sketch.pdf",
    "expected_validity": false,
    "expected_document_type": null,
    "notes": "Just a rough sketch, not a proper planning drawing"
  }
]
```

### Import Ground Truth

```bash
# From JSON file
python examples/manage_ground_truth.py import ground_truth.json

# Via API
curl -X POST http://localhost:8000/api/ground-truth/import \
  -F "file=@ground_truth.json"
```

### Export Ground Truth

```bash
# To JSON file
python examples/manage_ground_truth.py export all_labels.json

# Via API
curl http://localhost:8000/api/ground-truth/export > labels.json
```

### List Ground Truth

```bash
python examples/manage_ground_truth.py list
```

## Viewing Results

### List All Runs

```bash
# Via API
curl http://localhost:8000/api/runs | jq '.'

# Using httpx (Python)
import httpx
response = httpx.get("http://localhost:8000/api/runs")
runs = response.json()
```

### Get Run Details

```bash
# Via API
curl http://localhost:8000/api/runs/{run_id} | jq '.'

# Via web interface
# Open: http://localhost:8000/runs/{run_id}
```

### Export Run Results

```bash
# Download as JSON
curl http://localhost:8000/api/runs/{run_id}/export?format=json > run_results.json

# Download as CSV
curl http://localhost:8000/api/runs/{run_id}/export?format=csv > run_results.csv

# Download as Excel
curl http://localhost:8000/api/runs/{run_id}/export?format=xlsx > run_results.xlsx
```

## Real-time Updates

The evaluation app uses WebSockets for real-time progress updates.

### JavaScript Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'evaluation_started':
      console.log('Evaluation started:', data.run_id);
      break;

    case 'document_complete':
      console.log('Document complete:', data.document_id);
      console.log('Progress:', data.progress);
      break;

    case 'evaluation_complete':
      console.log('Evaluation complete!');
      console.log('Accuracy:', data.overall_accuracy);
      break;

    case 'evaluation_error':
      console.error('Error:', data.error);
      break;
  }
};
```

### Python Example

```python
import asyncio
import websockets
import json

async def watch_evaluation():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "document_complete":
                print(f"Progress: {data['completed']}/{data['total']}")

            elif data["type"] == "evaluation_complete":
                print(f"Accuracy: {data['overall_accuracy']:.1%}")
                break

asyncio.run(watch_evaluation())
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost/db"  # pragma: allowlist secret

# Storage
STORAGE_TYPE="s3"  # or "local"
AWS_REGION="eu-west-2"
S3_BUCKET_NAME="my-bucket"

# LLM
ANTHROPIC_API_KEY="sk-ant-..."  # pragma: allowlist secret
LLM_MODEL="claude-3-5-sonnet-20241022"
LLM_TEMPERATURE="0.0"

# Evaluation
DOCUMENT_CONCURRENCY="5"  # Number of parallel validations
```

### Configuration File

Alternatively, create `config.yaml`:

```yaml
database:
  url: postgresql://user:password@localhost/db  # pragma: allowlist secret

storage:
  type: s3
  aws_region: eu-west-2
  s3_bucket_name: my-bucket

llm:
  model: claude-3-5-sonnet-20241022
  temperature: 0.0
  enable_thinking: true

evaluation:
  document_concurrency: 5
```

## Common Workflows

### 1. Evaluate a Batch of Documents

```bash
# 1. Upload documents to storage
# 2. Create document records in database
# 3. Start evaluation
curl -X POST http://localhost:8000/api/evaluation/start \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["doc1", "doc2", "doc3"]}'

# 4. Watch progress via WebSocket
# 5. Download results when complete
curl http://localhost:8000/api/runs/{run_id}/export?format=json > results.json
```

### 2. Compare Multiple Runs

```bash
# Get run summaries
curl http://localhost:8000/api/runs | jq '.[] | {run_id, accuracy: .overall_accuracy, timestamp}'

# Compare specific runs
curl http://localhost:8000/api/runs/compare?run_ids=run1,run2 | jq '.'
```

### 3. Evaluate with Ground Truth

```bash
# 1. Import ground truth labels
python examples/manage_ground_truth.py import labels.json

# 2. Run evaluation (will automatically use ground truth if available)
curl -X POST http://localhost:8000/api/evaluation/start \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["doc1", "doc2"]}'

# 3. View accuracy metrics
curl http://localhost:8000/api/runs/{run_id} | jq '.overall_accuracy'
```

## Troubleshooting

**Issue**: Database connection error
- **Solution**: Check `DATABASE_URL` is set correctly and database is running

**Issue**: Storage upload fails
- **Solution**: Verify AWS credentials or local storage path permissions

**Issue**: WebSocket connection fails
- **Solution**: Ensure web server is running and firewall allows WebSocket connections

**Issue**: Low accuracy
- **Solution**: Review ground truth labels, try different LLM model, enable extended thinking

## Performance Tips

1. **Adjust concurrency**: Set `DOCUMENT_CONCURRENCY` based on your LLM rate limits
2. **Use database connection pooling**: For high-volume evaluations
3. **Monitor costs**: Check carbon impact and LLM API usage
4. **Batch operations**: Process documents in batches rather than one at a time

## Next Steps

- See [API documentation](./api_examples.md)
- See [Architecture overview](../docs/ARCHITECTURE.md)
- See [Deployment guide](../docs/DEPLOYMENT.md)

## Support

For issues: [GitHub Issues](https://github.com/your-org/planning-drawing-validator/issues)
