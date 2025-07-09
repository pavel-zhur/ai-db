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
COPY console /workspace/console

# Change to console directory
WORKDIR /workspace/console

# Install dependencies
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Component-specific command
CMD ["console"]