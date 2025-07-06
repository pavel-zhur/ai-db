FROM ai-db-system:base

# Copy only this component
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev

COPY src/ ./src/

# Component-specific command
# Default to ai-db-mcp, can be overridden
CMD ["ai-db-mcp"]