#!/bin/bash
# Test runner script for Docker environment
# Run unit tests inside the web container

set -e

echo "=========================================="
echo "Asset Management System - Test Runner"
echo "=========================================="
echo ""

# Check if Docker Compose is running
if ! docker compose ps | grep -q "web.*running"; then
    echo "❌ Error: Docker Compose web service is not running"
    echo ""
    echo "Start the dev stack first:"
    echo "  docker compose --profile dev up -d --build"
    echo ""
    exit 1
fi

echo "✓ Docker Compose is running"
echo ""

# Run tests with verbose output
echo "Running test suite..."
echo ""

docker compose exec web python manage.py test assets -v 2

EXIT_CODE=$?

echo ""
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed with exit code $EXIT_CODE"
fi

echo "=========================================="

exit $EXIT_CODE
