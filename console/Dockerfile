FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory to parent level to maintain relative paths
WORKDIR /workspace

# Stage 1: Copy only pyproject.toml, poetry.lock, and README files for dependency installation
# This allows Docker to cache the poetry install layer if dependencies don't change

# Copy dependency package structures first (minimal files needed for poetry to recognize packages)
COPY ai-shared/pyproject.toml ai-shared/poetry.lock* ai-shared/README.md /workspace/ai-shared/
COPY ai-shared/src/ai_shared/__init__.py /workspace/ai-shared/src/ai_shared/

COPY ai-db/pyproject.toml ai-db/poetry.lock* ai-db/README.md /workspace/ai-db/
COPY ai-db/src/ai_db/__init__.py /workspace/ai-db/src/ai_db/

COPY ai-frontend/pyproject.toml ai-frontend/poetry.lock* ai-frontend/README.md /workspace/ai-frontend/
COPY ai-frontend/src/ai_frontend/__init__.py /workspace/ai-frontend/src/ai_frontend/

COPY git-layer/pyproject.toml git-layer/poetry.lock* git-layer/README.md /workspace/git-layer/
COPY git-layer/src/git_layer/__init__.py /workspace/git-layer/src/git_layer/

COPY console/pyproject.toml console/poetry.lock* console/README.md /workspace/console/
COPY console/src/console/__init__.py /workspace/console/src/console/

# Change to console directory and install dependencies
WORKDIR /workspace/console
RUN poetry install --only main && rm -rf $POETRY_CACHE_DIR

# Stage 2: Copy the full source code
# This happens after poetry install, so source changes won't invalidate the dependency cache
COPY ai-shared /workspace/ai-shared
COPY ai-db /workspace/ai-db
COPY ai-frontend /workspace/ai-frontend
COPY git-layer /workspace/git-layer
COPY console /workspace/console

# Component-specific command
CMD ["console"]