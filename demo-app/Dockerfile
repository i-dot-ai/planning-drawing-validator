# ============================================================================
# Demo App Dockerfile - Multi-stage build
# ============================================================================
# Directory structure mirrors local dev so [tool.uv.sources] paths work:
#   /repo/planning-drawing-validator/
#   /repo/demo-app/  <- "../planning-drawing-validator" resolves correctly
# ============================================================================

FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ============================================================================
# Stage 2: Install core package first
# ============================================================================
FROM base AS core

# Copy core package to mirror local structure
COPY planning-drawing-validator/ /repo/planning-drawing-validator/

# Install core package
RUN uv pip install --system /repo/planning-drawing-validator

# ============================================================================
# Stage 3: Install demo app
# ============================================================================
FROM core AS demo

# Copy demo app to mirror local structure
# Now "../planning-drawing-validator" resolves to /repo/planning-drawing-validator
COPY demo-app/ /repo/demo-app/

WORKDIR /repo/demo-app

# Install demo app dependencies
RUN uv pip install --system -e .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Expose port
EXPOSE 8001

# Run the demo API
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8001"]
