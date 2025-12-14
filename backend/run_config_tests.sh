#!/bin/bash

# Script to run configuration tests
# This verifies that the config loading works correctly with Python 3.13 and pydantic-settings 2.7.1

set -e

echo "======================================"
echo "Running Configuration Tests"
echo "======================================"
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-asyncio
fi

echo "✓ pytest is available"
echo ""

# Run the config tests
echo "Running test_config.py..."
echo ""

pytest tests/test_config.py -v --tb=short

echo ""
echo "======================================"
echo "✅ All configuration tests passed!"
echo "======================================"
