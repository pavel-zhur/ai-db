FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy local dependencies from parent directory context
# NOTE: Docker build should be run from workspace root with: docker build -f ai-frontend/Dockerfile .
COPY ai-shared ./ai-shared

# Copy component-specific files
COPY ai-frontend/pyproject.toml ai-frontend/poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy component source code
COPY ai-frontend/src/ ./src/

# Check if templates directory exists
COPY ai-frontend/templates* ./templates/

# Component-specific command
CMD ["python", "-m", "ai_frontend"]