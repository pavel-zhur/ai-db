# AI-DB/AI-Frontend MCP Servers

This package provides Model Context Protocol (MCP) servers for AI-DB and AI-Frontend, exposing their functionality to MCP-compatible AI tools.

## Overview

The package includes two separate MCP servers:

1. **AI-DB MCP Server** (`ai-db-mcp`) - Exposes database operations
2. **AI-Frontend MCP Server** (`ai-frontend-mcp`) - Exposes frontend generation

## Installation

```bash
pip install -e .
```

For development with mock implementations:
```bash
pip install -e ".[dev]"
```

## Usage

### AI-DB MCP Server

```bash
# With real implementations (when available)
ai-db-mcp

# With mock implementations (for testing)
AI_DB_USE_MOCKS=true ai-db-mcp
```

### AI-Frontend MCP Server

```bash
# With real implementations (when available)
ai-frontend-mcp

# With mock implementations (for testing)
AI_FRONTEND_USE_MOCKS=true ai-frontend-mcp
```

## Available Tools

### AI-DB Tools

1. **schema_modify** - Modify table schemas, relationships, and constraints
2. **data_modify** - Insert, update, and delete data
3. **select** - Execute queries with joins and aggregations
4. **view_modify** - Create and modify views
5. **execute_compiled** - Execute pre-compiled query plans
6. **begin_transaction** - Start a new transaction
7. **commit_transaction** - Commit an active transaction
8. **rollback_transaction** - Rollback an active transaction
9. **get_schema** - Get current database schema with semantic descriptions

### AI-Frontend Tools

1. **generate_frontend** - Generate or modify React components using natural language
2. **get_frontend_info** - Get information about generated components

## Configuration

Configuration can be set via environment variables:

### AI-DB Server

- `AI_DB_LOG_LEVEL` - Logging level (default: INFO)
- `AI_DB_LOG_FORMAT` - Log format: "json" or "console" (default: json)
- `AI_DB_USE_MOCKS` - Use mock implementations (default: false)
- `AI_DB_GIT_REPO_PATH` - Git repository path (default: /workspace/data)
- `AI_DB_MAX_RETRY_ATTEMPTS` - Max retry attempts for operations (default: 3)
- `AI_DB_OPERATION_TIMEOUT` - Operation timeout in seconds (default: 300)

### AI-Frontend Server

- `AI_FRONTEND_LOG_LEVEL` - Logging level (default: INFO)
- `AI_FRONTEND_LOG_FORMAT` - Log format: "json" or "console" (default: json)
- `AI_FRONTEND_USE_MOCKS` - Use mock implementations (default: false)
- `AI_FRONTEND_GIT_REPO_PATH` - Git repository path (default: /workspace/frontend)
- `AI_FRONTEND_CLAUDE_CODE_TIMEOUT` - Claude Code timeout in seconds (default: 600)

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src tests
```

### Code Formatting

```bash
black src tests
ruff check src tests
```

## Architecture

The MCP servers follow these principles:

1. **Separate Servers** - AI-DB and AI-Frontend run as independent MCP servers
2. **Tool-Based Interface** - Each operation is exposed as a discrete MCP tool
3. **Transaction Support** - Optional transaction support for grouped operations
4. **Type Safety** - Full type annotations with Pydantic models
5. **Mock Support** - Built-in mocks for testing and development

## Integration with MCP Clients

The servers use stdio transport and can be integrated with any MCP-compatible client. Example configuration for Claude Desktop:

```json
{
  "mcpServers": {
    "ai-db": {
      "command": "ai-db-mcp",
      "env": {
        "AI_DB_USE_MOCKS": "true"
      }
    },
    "ai-frontend": {
      "command": "ai-frontend-mcp",
      "env": {
        "AI_FRONTEND_USE_MOCKS": "true"
      }
    }
  }
}
```

## License

[License information here]