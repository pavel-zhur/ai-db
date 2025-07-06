FROM ai-db-system:base

# Copy only this component
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev

COPY src/ ./src/

# Component-specific command
CMD ["uvicorn", "ai_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]