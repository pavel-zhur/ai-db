# AI-DB/AI-Frontend MCP Servers

This package provides Model Context Protocol (MCP) servers for AI-DB and AI-Frontend, exposing their functionality to MCP-compatible AI tools like Claude Desktop.

## Overview

The package includes two separate MCP servers:

1. **AI-DB MCP Server** - Exposes database operations with full CRUD, schema management, and transaction support
2. **AI-Frontend MCP Server** - Exposes React frontend generation and management capabilities

Both servers use the standardized `TransactionProtocol` from ai-shared for consistent transaction management across the ecosystem.

## Installation

```bash
# Navigate to the MCP directory
cd /workspace/mcp

# Install with Poetry (recommended)
poetry install

# Or install with pip
pip install -e .
```

## Usage

### Running with Poetry (Recommended)

```bash
# AI-DB MCP Server
poetry run python -m ai_mcp.ai_db_server

# AI-Frontend MCP Server  
poetry run python -m ai_mcp.ai_frontend_server

# With mocks for testing
AI_DB_USE_MOCKS=true poetry run python -m ai_mcp.ai_db_server
AI_FRONTEND_USE_MOCKS=true poetry run python -m ai_mcp.ai_frontend_server
```

### Programmatic Usage

```python
import asyncio
from ai_mcp import create_ai_db_server, create_ai_frontend_server
from ai_mcp import AIDBMCPConfig, AIFrontendMCPConfig

async def main():
    # Create AI-DB server
    db_config = AIDBMCPConfig(use_mocks=True)
    db_server = await create_ai_db_server(db_config)
    
    # Create AI-Frontend server
    frontend_config = AIFrontendMCPConfig(use_mocks=True)
    frontend_server = await create_ai_frontend_server(frontend_config)

asyncio.run(main())
```

## Available Tools

### AI-DB Tools

1. **schema_modify** - Modify database schemas, tables, and relationships
2. **data_modify** - Insert, update, and delete data operations
3. **select** - Execute SELECT queries with joins and aggregations
4. **view_modify** - Create and modify database views
5. **execute_compiled** - Execute pre-compiled query plans for performance
6. **compile_query** - Compile natural language to optimized query plans
7. **get_schema** - Get current database schema with semantic descriptions
8. **init_from_folder** - Initialize database from existing schema files

### AI-Frontend Tools

1. **generate_frontend** - Generate complete React frontends from natural language requests
2. **update_frontend** - Update existing frontends with new requirements
3. **get_frontend_schema** - Get current frontend schema and structure
4. **init_frontend_from_folder** - Initialize frontend from existing seed files

## Configuration

Configuration uses Pydantic BaseSettings with environment variable support:

### Environment Variables

The MCP servers use **independent environment variable namespaces** to avoid conflicts:

#### MCP Server Settings
- `AI_DB_MCP_LOG_LEVEL` - AI-DB MCP server logging level (default: INFO)
- `AI_DB_MCP_LOG_FORMAT` - AI-DB MCP log format: "json" or "console" (default: json)
- `AI_DB_MCP_USE_MOCKS` - Use mock implementations for AI-DB MCP (default: false)
- `AI_DB_MCP_REPO_PATH` - Git repository path for AI-DB MCP (default: /workspace/data)

- `AI_FRONTEND_MCP_LOG_LEVEL` - AI-Frontend MCP server logging level (default: INFO)
- `AI_FRONTEND_MCP_LOG_FORMAT` - AI-Frontend MCP log format: "json" or "console" (default: json)
- `AI_FRONTEND_MCP_USE_MOCKS` - Use mock implementations for AI-Frontend MCP (default: false)
- `AI_FRONTEND_MCP_REPO_PATH` - Git repository path for AI-Frontend MCP (default: /workspace/frontend)

#### AI-DB Library Settings (Independent)
The ai-db library reads its own configuration with `AI_DB_` prefix:
- `AI_DB_API_KEY` - AI API key for query processing
- `AI_DB_API_BASE` - AI API base URL (default: https://api.openai.com/v1)
- `AI_DB_MODEL` - AI model to use (default: gpt-4)
- `AI_DB_TEMPERATURE` - AI temperature setting (default: 0.1)
- `AI_DB_TIMEOUT_SECONDS` - AI API timeout (default: 30)
- `AI_DB_MAX_RETRIES` - AI API max retries (default: 3)

#### AI-Frontend Library Settings (Independent)
The ai-frontend library reads its own configuration with `AI_FRONTEND_` prefix:
- `AI_FRONTEND_CLAUDE_CODE_DOCKER_IMAGE` - Docker image (default: anthropics/claude-code:latest)
- `AI_FRONTEND_MAX_ITERATIONS` - Max generation iterations (default: 5)
- `AI_FRONTEND_TIMEOUT_SECONDS` - Timeout in seconds (default: 300)
- `AI_FRONTEND_USE_MATERIAL_UI` - Use Material-UI (default: true)
- `AI_FRONTEND_TYPESCRIPT_STRICT` - Use strict TypeScript (default: true)

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test suites
poetry run pytest tests/integration/
poetry run pytest tests/unit/
```

### Code Quality

```bash
# Type checking
poetry run mypy .

# Linting
poetry run ruff check .

# Formatting
poetry run black .

# Fix linting issues
poetry run ruff check --fix .
```

## Architecture

### Key Design Principles

1. **Standards Compliance** - Uses ai-shared.TransactionProtocol for transaction management
2. **Real Library Integration** - Direct integration with ai-db, ai-frontend, and git-layer
3. **Type Safety** - Comprehensive type annotations with Pydantic models
4. **Async/Await** - Proper async patterns throughout for performance
5. **Mock Support** - Built-in mocks for testing and development
6. **Tool-Based Interface** - Each operation exposed as a discrete MCP tool

### Transaction Management

Both servers use the standardized TransactionProtocol:

```python
async with self._create_transaction("Operation description") as transaction:
    result = await self._ai_db.execute(query, permissions, transaction)
    # Transaction auto-commits on success, rolls back on exception
```

### Error Handling

Follows CLAUDE.md guidelines:
- Let exceptions propagate to appropriate boundary layers
- Use structured logging with different levels (ERROR, WARN, INFO)
- Trust the type system - avoid defensive programming

## Integration Requirements

### Dependencies

When running without mocks, these packages must be available:

- `ai-shared` - Shared protocols and interfaces
- `ai-db` - AI-DB core engine (from `/workspace/ai-db`)
- `ai-frontend` - AI-Frontend engine (from `/workspace/ai-frontend`)
- `git-layer` - Git transaction support (from `/workspace/git-layer`)

### MCP Client Integration

Example Claude Desktop configuration:

```json
{
  "mcpServers": {
    "ai-db": {
      "command": "poetry",
      "args": ["run", "python", "-m", "ai_mcp.ai_db_server"],
      "cwd": "/workspace/mcp",
      "env": {
        "AI_DB_MCP_USE_MOCKS": "true",
        "AI_DB_API_KEY": "your-openai-api-key",
        "AI_DB_MODEL": "gpt-4"
      }
    },
    "ai-frontend": {
      "command": "poetry", 
      "args": ["run", "python", "-m", "ai_mcp.ai_frontend_server"],
      "cwd": "/workspace/mcp",
      "env": {
        "AI_FRONTEND_MCP_USE_MOCKS": "true",
        "AI_FRONTEND_MAX_ITERATIONS": "3"
      }
    }
  }
}
```

## Package Structure

```
src/ai_mcp/
├── __init__.py          # Main exports
├── ai_db_server.py      # AI-DB MCP server
├── ai_frontend_server.py # AI-Frontend MCP server  
├── config.py            # Pydantic configuration classes
├── protocols.py         # Protocol interfaces
├── models/              # Pydantic data models
├── tools/               # MCP tool implementations
│   ├── ai_db/          # AI-DB tools
│   └── ai_frontend/    # AI-Frontend tools
└── mocks/              # Mock implementations for testing
```

## License

MIT License - See LICENSE file for details.