#!/bin/bash

set -e

echo "Running flake8..."
flake8 apps/ config/

echo "Checking formatting with black..."
black --check apps/ config/

echo "Checking import order with isort"
isort --check-only apps/ config/

echo "Linting checks passed!"
