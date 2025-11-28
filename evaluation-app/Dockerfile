# ============================================================================
# Evaluation App Dockerfile - Multi-stage build
# ============================================================================
# Directory structure mirrors local dev so [tool.uv.sources] paths work:
#   /repo/planning-drawing-validator/
#   /repo/evaluation-app/  <- "../planning-drawing-validator" resolves correctly
# ============================================================================

FROM python:3.14-slim AS base

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
# Stage 3: Install evaluation app
# ============================================================================
FROM core AS evaluation

# Copy evaluation app to mirror local structure
# Now "../planning-drawing-validator" resolves to /repo/planning-drawing-validator
COPY evaluation-app/ /repo/evaluation-app/

WORKDIR /repo/evaluation-app

# Install evaluation app dependencies
RUN uv pip install --system -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser && \
    chown -R appuser:appuser /repo

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run the evaluation web server
CMD ["uvicorn", "backend.web_server:app", "--host", "0.0.0.0", "--port", "8000"]
