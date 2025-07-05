FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all projects (assuming they're built into the container)
COPY ai-db /app/ai-db
COPY ai-frontend /app/ai-frontend
COPY git-layer /app/git-layer
COPY console /app/console

# Install Python dependencies for all projects
RUN pip install --no-cache-dir -e /app/git-layer && \
    pip install --no-cache-dir -e /app/ai-db && \
    pip install --no-cache-dir -e /app/ai-frontend && \
    pip install --no-cache-dir -e /app/console

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV GIT_LAYER_REPO_PATH=/data
ENV CONSOLE_LOG_FILE=/data/console.log
ENV CONSOLE_TRACE_FILE=/data/console_trace.log

# Create console wrapper script
RUN echo '#!/bin/bash\npython -m console.main "$@"' > /usr/local/bin/console && \
    chmod +x /usr/local/bin/console

# Volume for data persistence
VOLUME ["/data"]

# Default command
CMD ["console"]