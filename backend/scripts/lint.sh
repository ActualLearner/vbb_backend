#!/bin/bash

set -e

echo "Running ruff check..."
ruff check apps/ config/ tests/ manage.py

echo "Checking formatting with ruff format..."
ruff format --check apps/ config/ tests/ manage.py

echo "Linting checks passed!"
