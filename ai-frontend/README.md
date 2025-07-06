# AI-Frontend

A Python library for generating and managing static React frontends using AI. Works like SQLite - embed it in your application to create TypeScript/React interfaces from database schemas and natural language requests.

## Features

- 🎯 **Natural Language to UI**: Describe your interface in plain English
- 📊 **Schema-Driven**: Automatically generates TypeScript types from JSON Schema
- ⚡ **React + TypeScript**: Modern frontend stack with Material-UI
- 🔧 **Transaction-Safe**: Integrates with git-layer for atomic operations
- 🐳 **Docker-Based**: Uses Claude Code CLI in isolated containers
- 🧪 **Fully Tested**: Comprehensive test suite with 31 tests

## Quick Start

### Installation

```bash
cd ai-frontend
poetry install
```

### Basic Usage

```python
from pathlib import Path
from ai_frontend import AiFrontend, AiFrontendConfig

# Configure the library
config = AiFrontendConfig(
    api_base_url="http://localhost:8000",
    claude_code_docker_image="anthropics/claude-code:latest"
)

# Create frontend generator
frontend = AiFrontend(config)

# Generate a frontend (within a transaction)
async with git_layer.begin_transaction() as transaction:
    result = await frontend.generate_frontend(
        request="Create a user management dashboard with table view and forms",
        schema=your_json_schema,
        transaction=transaction,
        project_name="user-portal"
    )
    
    if result.success:
        print(f"Frontend generated at: {result.output_path}")
    else:
        print(f"Error: {result.error}")
```

## Configuration

The library uses pydantic BaseSettings for configuration. Set via environment variables with `AI_FRONTEND_` prefix:

```bash
# Claude Code settings
export AI_FRONTEND_CLAUDE_CODE_DOCKER_IMAGE="anthropics/claude-code:latest"
export AI_FRONTEND_MAX_ITERATIONS=5
export AI_FRONTEND_TIMEOUT_SECONDS=300
export AI_FRONTEND_RETRY_ATTEMPTS=2

# Frontend settings  
export AI_FRONTEND_API_BASE_URL="http://localhost:8000"
export AI_FRONTEND_USE_MATERIAL_UI=true
export AI_FRONTEND_TYPESCRIPT_STRICT=true

# Logging
export AI_FRONTEND_LOG_LEVEL="INFO"
```

Or use a `.env` file:

```ini
AI_FRONTEND_API_BASE_URL=http://localhost:8000
AI_FRONTEND_MAX_ITERATIONS=3
AI_FRONTEND_LOG_LEVEL=DEBUG
```

## Core Methods

### `generate_frontend()`

Creates a complete React frontend from scratch:

```python
result = await frontend.generate_frontend(
    request="Create a customer relationship management interface",
    schema=crm_schema,           # JSON Schema format
    transaction=transaction,      # From git-layer
    project_name="crm-portal"
)
```

**Generated Structure:**
```
frontend/
├── package.json          # Dependencies (React, TypeScript, Material-UI, Vite)
├── vite.config.ts        # Build configuration
├── tsconfig.json         # TypeScript settings
├── src/
│   ├── main.tsx          # Entry point
│   ├── App.tsx           # Main component (Claude-generated)
│   ├── types/api.ts      # Generated TypeScript interfaces
│   └── services/         # API client with retry logic
└── .gitignore           # Proper ignore patterns
```

### `update_frontend()`

Updates an existing frontend:

```python
result = await frontend.update_frontend(
    request="Add search and filtering to the user table",
    schema=updated_schema,
    transaction=transaction
)
```

### `get_schema()`

Retrieves the current schema stored with the frontend:

```python
current_schema = await frontend.get_schema(transaction)
```

### `init_from_folder()`

Initialize frontend from existing React project:

```python
await frontend.init_from_folder(
    source_path=Path("./my-existing-react-app"),
    transaction=transaction
)
```

## API Integration

Generated frontends connect to your AI-DB API server using these endpoints:

- `POST /db/query` - Execute compiled queries
- `POST /db/query/view` - Execute named views  
- `POST /db/data` - Data modifications (INSERT/UPDATE/DELETE)

Example API client usage in generated frontend:
```typescript
// Generated in src/services/
const users = await userService.getAll();
const user = await userService.getById("123");
await userService.create({name: "John", email: "john@example.com"});
```

## Schema Format

Uses JSON Schema standard stored as YAML:

```yaml
tables:
  users:
    columns:
      id:
        type: integer
        primary_key: true
        auto_increment: true
      name:
        type: string
        required: true
      email:
        type: string
        format: email
        required: true
      created_at:
        type: string
        format: date-time
```

**Generates TypeScript:**
```typescript
export interface User {
  id: number;
  name: string;
  email: string;
  created_at?: string;
}

export interface CreateUserDTO {
  name: string;
  email: string;
  created_at?: string;
}

export interface UpdateUserDTO {
  name?: string;
  email?: string;
}
```

## Transaction Integration

AI-Frontend integrates with git-layer for atomic operations:

```python
from ai_shared.protocols import TransactionProtocol

async with git_layer.begin_transaction() as transaction:
    # All operations in this block are atomic
    
    # Generate frontend
    result = await frontend.generate_frontend(...)
    
    # If any operation fails, entire transaction rolls back
    # If all succeed, transaction commits automatically
```

**Transaction Events:**
- `await transaction.write_escalation_required()` - Request write permissions
- `await transaction.operation_complete(message)` - Mark success
- `await transaction.operation_failed(error)` - Mark failure

## Error Handling

The library follows a fail-fast approach with clear error messages:

```python
try:
    result = await frontend.generate_frontend(...)
    if not result.success:
        print(f"Generation failed: {result.error}")
        # Technical details available in logs
except Exception as e:
    print(f"Unexpected error: {e}")
    # Exception includes full context
```

**Error Categories:**
- **Configuration errors**: Invalid settings or missing dependencies
- **Schema errors**: Invalid JSON Schema format
- **Generation errors**: Claude Code failures or timeouts
- **Compilation errors**: TypeScript compilation failures
- **Transaction errors**: Git operations or permission issues

## Development

### Running Tests

```bash
poetry run pytest                    # All tests
poetry run pytest tests/test_core.py # Specific test file
poetry run pytest -v                # Verbose output
```

### Code Quality

```bash
poetry run mypy .                    # Type checking
poetry run ruff check .              # Linting
poetry run black .                   # Code formatting
```

### Environment Requirements

- **Python 3.13+**
- **Docker** (for Claude Code execution)
- **ANTHROPIC_API_KEY** environment variable

## Examples

### Basic CRM Interface

```python
crm_schema = {
    "tables": {
        "customers": {
            "columns": {
                "id": {"type": "integer", "primary_key": True},
                "name": {"type": "string", "required": True},
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        }
    }
}

async with git_layer.begin_transaction() as transaction:
    result = await frontend.generate_frontend(
        request="Create a customer management interface with a data table, search functionality, and forms for adding/editing customers",
        schema=crm_schema,
        transaction=transaction,
        project_name="crm-dashboard"
    )
```

### Blog Management System

```python
blog_schema = {
    "tables": {
        "posts": {
            "columns": {
                "id": {"type": "integer", "primary_key": True},
                "title": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
                "status": {"type": "string", "enum": ["draft", "published"]},
                "author_id": {"type": "integer"},
                "published_at": {"type": "string", "format": "date-time"}
            }
        }
    }
}

async with git_layer.begin_transaction() as transaction:
    result = await frontend.generate_frontend(
        request="Create a blog management interface with post editing, status management, and preview functionality",
        schema=blog_schema,
        transaction=transaction,
        project_name="blog-admin"
    )
```

### Updating Existing Frontend

```python
# After adding new fields to schema
updated_schema = {
    "tables": {
        "customers": {
            "columns": {
                # ... existing fields ...
                "avatar_url": {"type": "string", "format": "uri"},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

async with git_layer.begin_transaction() as transaction:
    result = await frontend.update_frontend(
        request="Add avatar display and tag management to the customer interface",
        schema=updated_schema,
        transaction=transaction
    )
```

## Deployment

Generated frontends are static and can be served by any web server:

```bash
# Build for production
cd frontend/
npm run build

# Serve with nginx
nginx -p . -c nginx.conf

# Or use Docker
docker run -p 80:80 -v $(pwd)/dist:/usr/share/nginx/html nginx
```

## Troubleshooting

### Common Issues

**"Claude Code timeout"**:
- Increase `timeout_seconds` in configuration
- Check Docker daemon is running
- Verify ANTHROPIC_API_KEY is valid

**"TypeScript compilation failed"**:
- Check schema format is valid JSON Schema
- Review error details in logs
- Try simplifying the request

**"No existing frontend found"**:
- Use `generate_frontend()` for new frontends
- Use `update_frontend()` only for existing ones

**"Transaction write permission denied"**:
- Ensure you're in a write transaction
- Check git repository permissions

### Debug Mode

Enable verbose logging:

```python
config = AiFrontendConfig(log_level="DEBUG")
```

Or via environment:
```bash
export AI_FRONTEND_LOG_LEVEL=DEBUG
```

## Contributing

1. Follow the coding standards in `/workspace/CLAUDE.md`
2. Add tests for new functionality
3. Run the full test suite: `poetry run pytest`
4. Ensure type checking passes: `poetry run mypy .`
5. Format code: `poetry run black .`

## License

This project is part of the AI-DB system. See the root repository for license information.