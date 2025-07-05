#!/bin/bash
# Helper script to run MCP servers

set -e

# Default to mock mode
USE_MOCKS=${USE_MOCKS:-true}

# Function to show usage
usage() {
    echo "Usage: $0 [ai-db|ai-frontend] [--no-mocks]"
    echo ""
    echo "Arguments:"
    echo "  ai-db         Run the AI-DB MCP server"
    echo "  ai-frontend   Run the AI-Frontend MCP server"
    echo ""
    echo "Options:"
    echo "  --no-mocks    Use real implementations instead of mocks"
    echo ""
    echo "Examples:"
    echo "  $0 ai-db                    # Run AI-DB server with mocks"
    echo "  $0 ai-frontend --no-mocks   # Run AI-Frontend server without mocks"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

SERVER=$1
shift

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-mocks)
            USE_MOCKS=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Run the appropriate server
case $SERVER in
    ai-db)
        echo "Starting AI-DB MCP server (mocks=$USE_MOCKS)..."
        export AI_DB_USE_MOCKS=$USE_MOCKS
        export AI_DB_LOG_FORMAT=console
        exec ai-db-mcp
        ;;
    ai-frontend)
        echo "Starting AI-Frontend MCP server (mocks=$USE_MOCKS)..."
        export AI_FRONTEND_USE_MOCKS=$USE_MOCKS
        export AI_FRONTEND_LOG_FORMAT=console
        exec ai-frontend-mcp
        ;;
    *)
        echo "Unknown server: $SERVER"
        usage
        ;;
esac