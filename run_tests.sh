#!/bin/bash
# Unix/Linux/Mac shell script to run tests

echo "========================================"
echo "OCR API Test Runner"
echo "========================================"
echo ""

# Check if server is running
echo "Checking if server is running..."
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "ERROR: Server is not running!"
    echo "Please start the server first:"
    echo "  python api.py"
    echo "  OR"
    echo "  python run_server.py"
    exit 1
fi

echo "Server is running!"
echo ""

# Run tests
if [ -z "$1" ]; then
    echo "Running basic tests (health check and languages)..."
    python test_api.py
else
    echo "Running tests with image: $1"
    python test_api.py "$1" "$2"
fi

