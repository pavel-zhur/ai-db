# Phase 1 Implementation - MCP Servers

## Overview

This document describes the Phase 1 implementation of the MCP servers for AI-DB and AI-Frontend. The implementation provides two separate Model Context Protocol servers that expose database and frontend generation capabilities to MCP-compatible AI tools.

## Architecture Decisions

### 1. Separate Servers
- **Decision**: Implemented as two independent MCP servers rather than a single unified server
- **Rationale**: As specified in requirements, this provides better separation of concerns and allows independent scaling/deployment
- **Implementation**: `ai-db-mcp` and `ai-frontend-mcp` as separate entry points

### 2. Protocol Interfaces
- **Decision**: Created formal protocol interfaces for all dependencies
- **Rationale**: Provides type safety and clear contracts without hard dependencies on implementation packages
- **Implementation**: `src/protocols.py` defines `AIDBProtocol`, `AIFrontendProtocol`, and `GitLayerProtocol`

### 3. Tool Organization
- **Decision**: Each database operation type is a separate tool (not unified)
- **Rationale**: Based on technical Q&A guidance and MCP best practices for atomic, focused tools
- **Tools**:
  - AI-DB: 9 tools (schema_modify, data_modify, select, view_modify, execute_compiled, begin_transaction, commit_transaction, rollback_transaction, get_schema)
  - AI-Frontend: 2 tools (generate_frontend, get_frontend_info)

### 4. Permission Inference
- **Decision**: Automatically infer permission levels from query content
- **Rationale**: Reduces client complexity as specified in requirements
- **Implementation**: `src/permission_inference.py` with pattern matching for different SQL operation types

### 5. Transaction Management
- **Decision**: Shared transaction state within each server instance
- **Rationale**: Enables transaction support across multiple tool calls
- **Implementation**: Shared dictionary for transaction contexts, passed between tools

## Implementation Details

### Project Structure
```
mcp/
├── src/
│   ├── __init__.py              # Package exports
│   ├── ai_db_server.py          # AI-DB MCP server
│   ├── ai_frontend_server.py    # AI-Frontend MCP server
│   ├── config.py                # Configuration management
│   ├── protocols.py             # Protocol interfaces
│   ├── permission_inference.py  # Permission level inference
│   ├── utils.py                 # Utility functions
│   ├── models/                  # Pydantic data models
│   │   ├── ai_db.py            # AI-DB request/response models
│   │   └── ai_frontend.py      # AI-Frontend request/response models
│   ├── tools/                   # Tool implementations
│   │   ├── ai_db/              # AI-DB tools
│   │   └── ai_frontend/        # AI-Frontend tools
│   └── mocks/                   # Mock implementations
├── tests/                       # Test suite
├── docs/                        # Documentation
└── requirements.txt             # Dependencies
```

### Key Components

#### 1. Server Implementation
- Uses official MCP Python SDK
- Stdio transport for local process communication
- Structured logging with JSON/console output options
- Graceful error handling with proper exit codes

#### 2. Tool Implementation
- Base class pattern for AI-DB tools with shared functionality
- Proper tool hints (destructiveHint, readOnlyHint)
- Comprehensive error handling and response formatting
- Transaction context management

#### 3. Configuration
- Environment-based configuration using Pydantic Settings
- CLI argument support for common options
- Separate configuration classes for each server

#### 4. Type Safety
- Full type annotations throughout
- Protocol interfaces for external dependencies
- Pydantic models for all request/response structures
- Generic base classes with type variables

## Assumptions Made

1. **Single-threaded within transactions**: While the server supports concurrent operations, we assume transactions are used in a single-threaded manner as specified

2. **Git-Layer transaction model**: Assumed that Git-Layer provides transaction IDs and manages the actual Git operations independently

3. **Natural language queries**: AI-DB is assumed to accept any natural language input, not just SQL

4. **Permission hierarchy**: Assumed SELECT < DATA_MODIFY < VIEW_MODIFY < SCHEMA_MODIFY

5. **Error response format**: Standardized error responses with `isError: true` in MCP TextContent

6. **Mock implementations**: Created comprehensive mocks that simulate the expected behavior of real implementations

## Integration Points

### Expected Interfaces

#### AI-DB (`ai_db` package)
```python
class AIDB:
    async def execute(query: str, permission_level: PermissionLevel, transaction_context: Optional[Any]) -> AIDBQueryResult
    async def execute_compiled(compiled_plan: str, transaction_context: Optional[Any]) -> AIDBQueryResult
    async def get_schema(include_semantic_docs: bool) -> dict[str, Any]
```

#### AI-Frontend (`ai_frontend` package)
```python
class AIFrontend:
    async def generate(request: str, transaction_context: Optional[Any]) -> AIFrontendResult
    async def get_frontend_info() -> dict[str, Any]
```

#### Git-Layer (`git_layer` package)
```python
class GitLayer:
    async def begin_transaction() -> str
    async def commit_transaction(transaction_id: str, commit_message: str) -> None
    async def rollback_transaction(transaction_id: str) -> None
```

## Testing Strategy

1. **Unit Tests**: Comprehensive tests for all tools, models, and utilities
2. **Integration Tests**: Server-level tests simulating MCP client interactions
3. **Mock Implementations**: Full mock implementations for development and testing
4. **Type Checking**: MyPy with strict settings
5. **Code Quality**: Black formatting and Ruff linting

## Deployment Options

1. **Local Installation**: pip install with entry points
2. **Docker**: Multi-stage Dockerfile for both servers
3. **Docker Compose**: For development with volumes
4. **Direct Execution**: Python module execution

## Open Questions and Clarifications Needed

1. **Transaction Context Structure**: What exactly should be passed as transaction_context to AI-DB and AI-Frontend? Currently using Any type.

2. **Compiled Query Plan Format**: What format do compiled query plans use? Assumed serialized strings.

3. **Schema Format**: What exact structure does AI-DB return for schemas? Assumed nested dictionaries.

4. **Error Recovery**: How should AI-DB errors be handled regarding transactions? Should failed operations automatically rollback?

5. **Progress Reporting**: Should long-running operations report progress? MCP supports progress tokens but not implemented yet.

6. **Resource URIs**: Should we implement MCP resource URIs for database objects?

7. **Atomic Operations**: For non-transactional operations, how does Git-Layer handle atomicity?

8. **Frontend Generation Context**: How does AI-Frontend know about the database schema? Through file system or should MCP pass it?

## Security Considerations

1. **No Authentication**: As specified, no auth in POC
2. **Permission Validation**: Inferred permissions prevent accidental destructive operations
3. **Input Validation**: All inputs validated through Pydantic models
4. **Safe Defaults**: Conservative permission inference (defaults to SELECT)

## Performance Considerations

1. **Stateless Design**: Each tool call is independent (except transactions)
2. **Concurrent Operations**: Server supports multiple concurrent operations
3. **Timeout Configuration**: Configurable timeouts for all operations
4. **Mock Performance**: Mocks return immediately for testing

## Future Enhancements

1. **Progress Reporting**: Add progress tokens for long operations
2. **Resource URIs**: Implement MCP resources for database objects
3. **Prompts**: Add MCP prompts for common operations
4. **Batch Operations**: Consider batch tool calls for efficiency
5. **WebSocket Transport**: Add support for remote connections
6. **Metrics**: Add operation metrics and monitoring

## Maintenance Notes

1. **Protocol Versioning**: Protocol interfaces allow evolution without breaking changes
2. **Mock Updates**: Mocks should be updated as real implementations evolve
3. **Test Coverage**: Maintain high test coverage for reliability
4. **Documentation**: Keep README and technical docs in sync with implementation