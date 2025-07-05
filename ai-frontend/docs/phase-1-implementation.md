# AI-Frontend Phase 1 Implementation Details

## Overview

AI-Frontend is a Python async library that generates React frontends using Claude Code CLI as the generation engine. It bridges AI-DB schemas with frontend generation, producing self-contained Material-UI based applications.

## Core Architecture

### Main Components

1. **AiFrontend (core.py)**: Main orchestrator that coordinates the generation workflow
2. **ClaudeCodeWrapper (claude_integration.py)**: Subprocess wrapper for Claude Code CLI
3. **SkeletonGenerator (skeleton_generator.py)**: Creates base React/Vite/TypeScript project
4. **TypeScriptGenerator (type_generator.py)**: Converts JSON Schema to TypeScript interfaces
5. **ApiGenerator (api_generator.py)**: Generates API client and React hooks
6. **FrontendCompiler (compiler.py)**: Validates generated code via npm build

### Generation Flow

1. Accept natural language request + AI-DB schema + git-layer transaction context
2. Generate React skeleton with Material-UI, Vite, TypeScript setup
3. Convert AI-DB schema to TypeScript types and API client code
4. Create context files (schema.yaml, api_types.ts) for Claude
5. Invoke Claude Code CLI with iterative refinement (max 5 iterations)
6. Claude generates components until SEMANTIC_DOCS.md indicates completion
7. Compile and validate the frontend
8. If compilation fails, give Claude one more chance to fix errors
9. Return success/failure with compilation status

## Key Implementation Decisions

### Claude Code Integration
- **Subprocess execution**: Using asyncio.create_subprocess_exec for CLI invocation
- **Iterative approach**: Multiple iterations until SEMANTIC_DOCS.md exists
- **Context provision**: Schema and types passed via temporary .claude_context directory
- **Isolation**: Using --no-interactive flag to prevent prompts

### TypeScript Generation
- **JSON Schema based**: AI-DB schemas follow JSON Schema format
- **Comprehensive types**: Interfaces for tables, views, DTOs, and API responses
- **Nullable handling**: Optional fields marked with ? in TypeScript
- **Enum support**: String enums converted to union types

### API Client Architecture
- **Retry logic**: 3 attempts for GET requests on 502/503/504 errors
- **Type safety**: Full TypeScript types for all API operations
- **Service pattern**: Separate service classes for each table
- **React hooks**: Custom hooks for data fetching with loading/error states

### Transaction Support
- **Git-layer integration**: All operations within transaction working directory
- **Commit message callback**: Optional callback for setting commit messages
- **Single-threaded**: No concurrency concerns per design
- **Isolation**: Each transaction gets its own workspace

## Assumptions Made

1. **Claude Code CLI availability**: Assumed to be installed and in PATH
2. **API server exists**: Frontend assumes AI-DB API server at configured URL
3. **Schema format**: AI-DB uses standard JSON Schema format
4. **Chrome MCP optional**: Visual feedback nice-to-have but not required
5. **Static generation**: No SSR, pure client-side React apps
6. **Material-UI standard**: Best for analytics dashboards per requirements
7. **Node.js 18+**: Modern Node version for Vite compatibility

## External Dependencies

### Required
- Claude Code CLI (command line tool)
- Node.js 18+ and npm
- Python 3.10+ with asyncio
- Git (for git-layer integration)

### Python Packages
- pydantic: Configuration management
- pyyaml: YAML file handling
- aiofiles: Async file I/O
- jsonschema: Schema validation

### Generated Frontend Dependencies
- React 18.2+
- Material-UI 5.15+
- Vite 5.0+
- TypeScript 5.3+
- Axios for API calls

## Interface Contracts

### Input Schema Format
```python
{
    "tables": {
        "table_name": {
            "columns": {
                "column_name": {
                    "type": "string|number|integer|boolean|array|object",
                    "format": "email|date|date-time|uuid",  # optional
                    "required": True|False,
                    "nullable": True|False,
                    "primary_key": True|False,
                    "foreign_key": "other_table.column",
                    # ... other JSON Schema properties
                }
            }
        }
    },
    "views": {
        "view_name": {
            "result_schema": {
                # Similar column definitions
            }
        }
    }
}
```

### Transaction Context
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path  # Where to generate files
    commit_message_callback: Optional[callable] = None
```

### API Endpoints Expected
- POST /api/query - For SELECT queries (permission: "select")
- POST /api/execute - For mutations (permission: "data_modify" | "schema_modify")

## Unanswered Questions

1. **MCP Chrome integration details**: How exactly does Chrome MCP communicate with Claude Code?
2. **AI-DB API authentication**: No auth mechanism specified - how will it work in production?
3. **Schema migration handling**: When schema changes, how to migrate existing frontends?
4. **Multi-tenant support**: Can one frontend connect to multiple AI-DB instances?
5. **Production deployment**: How will generated frontends be deployed (Docker, CDN, etc)?
6. **Monitoring/observability**: Should we add telemetry to generated frontends?
7. **Internationalization**: Will i18n be needed in future phases?

## Error Handling Strategy

1. **Generation failures**: Return detailed error messages with iteration count
2. **Compilation errors**: Extract TypeScript errors and attempt auto-fix
3. **Timeout handling**: 300-second default timeout for Claude Code operations
4. **Transaction rollback**: Relies on git-layer for cleanup on failure

## Future Considerations

1. **Caching**: Could cache generated components for similar requests
2. **Template library**: Pre-built component templates for common patterns
3. **Hot reload integration**: Development mode with auto-regeneration
4. **Component testing**: Generate tests alongside components
5. **Documentation hosting**: Auto-deploy generated docs
6. **Performance optimization**: Code splitting, lazy loading strategies

## Security Considerations

1. **Code execution**: Claude-generated code validated via compilation only
2. **API endpoints**: Parameterized to prevent injection (uses template literals)
3. **File system**: Operations restricted to transaction directory
4. **Subprocess isolation**: Claude Code runs with limited arguments

## Known Limitations

1. **Single-threaded**: No concurrent generation support
2. **Voice input**: Deferred to future phase
3. **Chrome-only**: Frontend targets Chrome browser
4. **English-only**: No i18n support in phase 1
5. **No testing**: Generated code lacks unit tests