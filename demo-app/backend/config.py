import os
from pathlib import Path

# Application settings
APP_NAME = "demo-validation-app"
APP_VERSION = "1.0.0"

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")  # nosec B104 - Intentionally bind to all interfaces in Docker
PORT = int(os.getenv("PORT", "8001"))

# Data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
UPLOAD_DIR = DATA_DIR / "uploads"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
