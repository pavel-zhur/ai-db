FROM ai-db-system:base

# Configure poetry for production
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory to parent level to maintain relative paths
WORKDIR /workspace

# Copy all required components maintaining directory structure
COPY ai-shared /workspace/ai-shared
COPY ai-db /workspace/ai-db
COPY git-layer /workspace/git-layer
COPY ai-hub /workspace/ai-hub

# Change to ai-hub directory
WORKDIR /workspace/ai-hub

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "ai_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]