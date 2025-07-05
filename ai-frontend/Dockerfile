FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI (placeholder - actual installation would depend on Claude Code distribution)
# RUN npm install -g @anthropic/claude-code-cli

# Set working directory
WORKDIR /app

# Copy Python package files
COPY pyproject.toml README.md ./
COPY ai_frontend ./ai_frontend

# Install Python package
RUN pip install --no-cache-dir -e .

# Create directories for frontend generation
RUN mkdir -p /workspace /tmp/ai-frontend

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Default command
CMD ["python", "-m", "ai_frontend"]