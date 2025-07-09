FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory to parent level to maintain relative paths
WORKDIR /workspace

# Copy all required components maintaining directory structure
COPY ai-shared /workspace/ai-shared
COPY ai-db /workspace/ai-db
COPY ai-frontend /workspace/ai-frontend
COPY git-layer /workspace/git-layer
COPY mcp /workspace/mcp

# Change to mcp directory
WORKDIR /workspace/mcp

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Component-specific command
# Default to ai-db-mcp, can be overridden
CMD ["ai-db-mcp"]