#!/bin/bash
# scripts/healthcheck.sh

echo "🔍 Checking AI-DB System environment..."
echo ""

# Check Python
if command -v python3.13 &> /dev/null; then
    echo "✅ Python 3.13 found"
else
    echo "❌ Python 3.13 not found (required)"
    exit 1
fi

# Check Poetry
if command -v poetry &> /dev/null; then
    echo "✅ Poetry found"
else
    echo "❌ Poetry not found - install with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
else
    echo "❌ Docker not found (required for running the system)"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✅ Git found"
else
    echo "❌ Git not found (required)"
    exit 1
fi

echo ""
echo "🎉 Environment ready for development!"