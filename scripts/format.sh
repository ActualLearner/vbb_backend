#!/bin/bash

set -e

echo "Formatting with black..."
black apps/ config/

echo "Sorting imports with isort..."
isort apps/ config/

echo "Formatting complete!"
