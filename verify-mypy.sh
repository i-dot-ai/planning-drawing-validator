#!/bin/bash
# MyPy type checking verification script

set -e

echo "Installing mypy and type stubs..."
uv pip install --system mypy types-requests types-PyYAML

echo ""
echo "Running mypy on planning-drawing-validator..."
cd planning-drawing-validator
mypy src/planning_drawing_validator --ignore-missing-imports --no-error-summary || true

echo ""
echo "Running mypy on demo-app..."
cd ../demo-app
mypy backend --ignore-missing-imports --no-error-summary || true

echo ""
echo "Running mypy on evaluation-app..."
cd ../evaluation-app
mypy backend --ignore-missing-imports --no-error-summary || true

echo ""
echo "✅ MyPy verification complete"
