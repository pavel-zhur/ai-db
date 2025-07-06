FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy local dependencies from parent directory context
# NOTE: Docker build should be run from workspace root with: docker build -f mcp/Dockerfile .
COPY ai-shared ./ai-shared
COPY ai-db ./ai-db
COPY ai-frontend ./ai-frontend
COPY git-layer ./git-layer

# Copy component-specific files
COPY mcp/pyproject.toml mcp/poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy component source code
COPY mcp/src/ ./src/

# Component-specific command
# Default to ai-db-mcp, can be overridden
CMD ["ai-db-mcp"]