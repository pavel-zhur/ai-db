FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy local dependencies from parent directory context
# NOTE: Docker build should be run from workspace root with: docker build -f ai-db/Dockerfile .
COPY ai-shared ./ai-shared

# Copy component-specific files
COPY ai-db/pyproject.toml ai-db/poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy component source code
COPY ai-db/src/ ./src/

# Component-specific command
CMD ["python", "-m", "ai_db"]