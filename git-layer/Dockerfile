FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy local dependencies from parent directory context
# NOTE: Docker build should be run from workspace root with: docker build -f git-layer/Dockerfile .
COPY ai-shared ./ai-shared

# Copy component-specific files
COPY git-layer/pyproject.toml git-layer/poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy component source code
COPY git-layer/src/ ./src/

# Component-specific command
CMD ["python", "-m", "git_layer"]