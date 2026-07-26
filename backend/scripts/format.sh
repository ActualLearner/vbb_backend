#!/bin/bash

set -e

echo "Fixing lint issues with ruff..."
ruff check --fix apps/ config/ tests/ manage.py

echo "Formatting with ruff..."
ruff format apps/ config/ tests/ manage.py

echo "Formatting complete!"
