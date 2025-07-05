# Multi-stage Dockerfile for MCP servers
FROM python:3.13-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install -e .

# AI-DB Server
FROM base as ai-db-server
ENV AI_DB_USE_MOCKS=false
ENV AI_DB_LOG_FORMAT=json
ENV AI_DB_GIT_REPO_PATH=/data
VOLUME ["/data"]
CMD ["ai-db-mcp"]

# AI-Frontend Server
FROM base as ai-frontend-server
ENV AI_FRONTEND_USE_MOCKS=false
ENV AI_FRONTEND_LOG_FORMAT=json
ENV AI_FRONTEND_GIT_REPO_PATH=/frontend
VOLUME ["/frontend"]
CMD ["ai-frontend-mcp"]