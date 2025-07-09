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

COPY git-layer/pyproject.toml git-layer/poetry.lock* git-layer/README.md /workspace/git-layer/
COPY git-layer/src/git_layer/__init__.py /workspace/git-layer/src/git_layer/

COPY ai-hub/pyproject.toml ai-hub/poetry.lock* ai-hub/README.md /workspace/ai-hub/
COPY ai-hub/src/ai_hub/__init__.py /workspace/ai-hub/src/ai_hub/

# Change to ai-hub directory and install dependencies
WORKDIR /workspace/ai-hub
RUN poetry install --only main && rm -rf $POETRY_CACHE_DIR

# Stage 2: Copy the full source code
# This happens after poetry install, so source changes won't invalidate the dependency cache
COPY ai-shared /workspace/ai-shared
COPY ai-db /workspace/ai-db
COPY git-layer /workspace/git-layer
COPY ai-hub /workspace/ai-hub

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "ai_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]