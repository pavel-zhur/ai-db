FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy dependency files from ai-hub directory
COPY ai-hub/pyproject.toml ai-hub/poetry.lock* ./

# Copy local dependencies from parent directory context
# NOTE: Docker build should be run from workspace root with: docker build -f ai-hub/Dockerfile .
COPY ai-shared ./ai-shared
COPY ai-db ./ai-db  
COPY git-layer ./git-layer

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Copy application code from ai-hub directory
COPY ai-hub/src/ ./src/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "ai_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]