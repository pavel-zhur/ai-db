# AI-Hub

HTTP API server for AI-DB frontend communication.

## Overview

AI-Hub provides a FastAPI-based HTTP interface for frontends to interact with AI-DB. It handles:
- Query execution
- Data modifications
- View execution

## API Endpoints

- `POST /db/query` - Execute compiled queries
- `POST /db/query/view` - Execute named views
- `POST /db/data` - Data modifications (INSERT/UPDATE/DELETE)

## Installation

```bash
poetry install
```

## Running

```bash
poetry run ai-hub
```

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run ruff check --fix .

# Type checking
poetry run mypy .
```