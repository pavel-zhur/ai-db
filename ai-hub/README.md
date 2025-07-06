# AI-Hub

HTTP API server for AI-DB frontend communication.

## Overview

AI-Hub provides a FastAPI-based HTTP interface for frontends to interact with AI-DB. It serves as the bridge between web frontends and the AI-DB system, handling query execution, data modifications, and view operations through a REST API.

### Key Features

- **AI-Native Query Processing**: Natural language queries are processed through AI-DB
- **Transaction Management**: Integrated with git-layer for version-controlled data operations
- **Progress Feedback**: Long-running operations provide periodic status updates
- **User-Friendly Error Handling**: Technical errors are translated to understandable messages
- **CORS Support**: Configured for cross-origin requests from frontend applications
- **Health Monitoring**: Built-in health check endpoints for deployment monitoring

## API Endpoints

### Query Execution
- `POST /db/query` - Execute natural language or compiled queries
- `POST /db/query/view` - Execute named views with parameters

### Data Operations
- `POST /db/data` - Data modifications (INSERT/UPDATE/DELETE operations)

### System
- `GET /health` - Health check endpoint
- `GET /` - API information

## Request/Response Models

### Query Request
```json
{
  "query": "SELECT all users where age > 25",
  "permissions": "read_write",
  "context": {
    "schema_version": "1.0",
    "error_history": []
  }
}
```

### View Query Request
```json
{
  "view_name": "active_users",
  "parameters": {"min_age": 25},
  "permissions": "read_only"
}
```

### Data Modification Request
```json
{
  "operation": "INSERT INTO users (name, age) VALUES ('John', 30)",
  "permissions": "read_write",
  "validate": true
}
```

### Response Format
```json
{
  "success": true,
  "data": [...],
  "data_loss_indicator": "none",
  "execution_time": 1.23,
  "transaction_id": "abc123"
}
```

### Error Response
```json
{
  "error": "User-friendly error message",
  "error_details": {
    "exception_type": "ValidationError",
    "technical_details": "..."
  },
  "error_type": "ValidationError"
}
```

## Configuration

Configuration is handled through environment variables or a `.env` file:

```bash
# Server Configuration
AI_HUB_HOST=0.0.0.0
AI_HUB_PORT=8000
AI_HUB_CORS_ORIGINS=["*"]

# Git Repository
AI_HUB_GIT_REPO_PATH=/data/repos

# AI-DB Configuration (maps to AI_DB_* environment variables)
AI_HUB_AI_DB_API_BASE=https://api.openai.com/v1
AI_HUB_AI_DB_API_KEY=your-openai-api-key
AI_HUB_AI_DB_MODEL=gpt-4
AI_HUB_AI_DB_TEMPERATURE=0.1
AI_HUB_AI_DB_TIMEOUT_SECONDS=60
AI_HUB_AI_DB_MAX_RETRIES=3

# Progress Feedback
AI_HUB_PROGRESS_FEEDBACK_INTERVAL=30
```

## Installation

### Prerequisites
- Python 3.13+
- Poetry 2.1.3+
- Git

### Local Development
```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the server
poetry run uvicorn ai_hub.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment
```bash
# Build base image first
docker build -f docker/base/Dockerfile -t ai-db-system:base .

# Build AI-Hub from workspace root
docker build -f ai-hub/Dockerfile -t ai-hub .

# Run container
docker run -p 8000:8000 \
  -e AI_HUB_AI_DB_API_KEY=your-key \
  -e AI_HUB_GIT_REPO_PATH=/data/repos \
  -v /path/to/repos:/data/repos \
  ai-hub
```

## Development

### Running Tests
```bash
# Install development dependencies
poetry install

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ai_hub --cov-report=html

# Run specific test file
poetry run pytest tests/test_endpoints.py
```

### Code Quality
```bash
# Format code
poetry run black .
poetry run ruff check --fix .

# Type checking
poetry run mypy .

# Run all quality checks
poetry run black . && poetry run ruff check --fix . && poetry run mypy . && poetry run pytest
```

### Integration Testing
Integration tests use real AI-DB and git-layer components but with mock AI services to avoid external dependencies.

```bash
# Run integration tests only
poetry run pytest tests/integration/

# Run with specific git repository
AI_HUB_GIT_REPO_PATH=/tmp/test-repo poetry run pytest tests/integration/
```

## Architecture

AI-Hub follows a layered architecture:

1. **Endpoints Layer** (`endpoints.py`): FastAPI route handlers
2. **Service Layer** (`service.py`): Business logic and AI-DB integration
3. **Models Layer** (`models.py`): Request/response schemas
4. **Configuration Layer** (`config.py`): Environment-based configuration
5. **Exception Layer** (`exceptions.py`): Error handling and user-friendly messages

### Dependencies
- **ai-db**: Core database engine with AI query processing
- **git-layer**: Version control and transaction management
- **ai-shared**: Common protocols and interfaces
- **FastAPI**: Web framework for REST API
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and serialization

## Usage Examples

### Basic Query
```bash
curl -X POST http://localhost:8000/db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all users created in the last week",
    "permissions": "read_only"
  }'
```

### View Execution
```bash
curl -X POST http://localhost:8000/db/query/view \
  -H "Content-Type: application/json" \
  -d '{
    "view_name": "monthly_sales",
    "parameters": {"year": 2024, "month": 12},
    "permissions": "read_only"
  }'
```

### Data Modification
```bash
curl -X POST http://localhost:8000/db/data \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "INSERT INTO products (name, price) VALUES (\"New Product\", 29.99)",
    "permissions": "read_write",
    "validate": true
  }'
```

## Troubleshooting

### Common Issues

**"poetry: command not found"**
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`

**"Permission denied on git repository"**
- Check git repository path configuration
- Ensure proper file permissions on the repository directory
- Verify the git repository is properly initialized

**"AI API key error"**
- Set the `AI_HUB_AI_DB_API_KEY` environment variable
- Verify the API key is valid for OpenAI
- Check network connectivity to api.openai.com

**"Long query timeout"**
- Increase the progress feedback interval
- Check query complexity and consider breaking into smaller operations
- Monitor logs for specific error details

### Logging
AI-Hub uses structured logging. Set log levels via environment:
```bash
AI_HUB_LOG_LEVEL=DEBUG poetry run uvicorn ai_hub.main:app
```

## Phase 2 AI-DB Compliance

AI-Hub is **fully compliant** with the updated AI-DB Phase 2 implementation:

- ✅ **Standardized Configuration**: Uses AI_DB_* environment variable pattern
- ✅ **Environment-based Integration**: AI-Hub translates its config to AI-DB environment variables
- ✅ **Compatible API Usage**: All AI-DB method calls use the latest interface
- ✅ **Production Ready**: Follows Phase 2 standardization requirements

### Configuration Mapping

AI-Hub environment variables are automatically mapped to AI-DB environment variables:

| AI-Hub Variable | AI-DB Variable | Description |
|----------------|----------------|-------------|
| `AI_HUB_AI_DB_API_KEY` | `AI_DB_API_KEY` | OpenAI API key |
| `AI_HUB_AI_DB_API_BASE` | `AI_DB_API_BASE` | API base URL |
| `AI_HUB_AI_DB_MODEL` | `AI_DB_MODEL` | AI model name |
| `AI_HUB_AI_DB_TEMPERATURE` | `AI_DB_TEMPERATURE` | AI temperature |
| `AI_HUB_AI_DB_TIMEOUT_SECONDS` | `AI_DB_TIMEOUT_SECONDS` | Request timeout |
| `AI_HUB_AI_DB_MAX_RETRIES` | `AI_DB_MAX_RETRIES` | Retry attempts |

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/
```