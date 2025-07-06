# AI-Frontend Phase 2 Implementation Details

This document provides detailed implementation information for future maintainer agents working on the ai-frontend component.

## Architecture Overview

The ai-frontend library follows the SQLite model - an embedded library that generates and manages static React frontends within transaction contexts. It operates independently from git-layer and ai-db while integrating seamlessly through the standardized TransactionProtocol from ai-shared.

## Core Components

### 1. AiFrontend (core.py)
**Primary Class**: Main library interface that orchestrates frontend generation.

**Key Methods**:
- `generate_frontend()` - Creates complete React frontend from natural language + schema
- `update_frontend()` - Updates existing frontend based on natural language requests
- `get_schema()` - Retrieves stored schema from frontend folder
- `init_from_folder()` - Initializes frontend from seed files with validation

**Transaction Integration**:
- Always calls `await transaction.write_escalation_required()` before writes
- Calls `await transaction.operation_complete(message)` on successful operations
- Calls `await transaction.operation_failed(error)` on failures
- Lets exceptions propagate naturally per CLAUDE.md guidelines

**Error Handling Philosophy**:
- Fail-fast approach - no graceful degradation
- Exceptions propagate to boundary layers (the main methods)
- User-friendly error messages with technical details logged
- Git-layer gets notified of all operation outcomes

### 2. ClaudeCodeWrapper (claude_integration.py)
**Purpose**: Manages Claude Code CLI execution in Docker containers.

**Docker Integration**:
- Uses `anthropics/claude-code:latest` (configurable)
- Mounts working directory and prompt file
- Passes through ANTHROPIC_API_KEY environment variable
- Isolated execution with automatic cleanup

**Progress Feedback**:
- Prints "Still working..." every 30 seconds (configurable)
- Handles timeouts gracefully (default 5 minutes)
- Async execution with proper cancellation

**Iteration Management**:
- Supports multiple Claude Code iterations (configurable max)
- Creates follow-up prompts for continued development
- Uses SEMANTIC_DOCS.md as completion indicator

### 3. TypeScriptGenerator (type_generator.py)
**Purpose**: Generates TypeScript interfaces from JSON Schema.

**Schema Compliance**:
- Follows JSON Schema standard (json-schema.org)
- Generates base interfaces, DTOs, and API response types
- Excludes auto-increment and primary key fields from UpdateDTOs
- Handles enums, arrays, nested objects, and optional fields

**Generated Types**:
- Base entity interfaces (e.g., `User`)
- CreateDTO interfaces (excluding auto-generated fields)
- UpdateDTO interfaces (excluding immutable/primary key fields)
- API response types (`ApiResponse<T>`, `QueryResult<T>`, `MutationResult`)

### 4. SkeletonGenerator (skeleton_generator.py)
**Purpose**: Creates React project structure with Vite, TypeScript, Material-UI.

**Generated Structure**:
```
frontend/
├── package.json          # Dependencies and scripts
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
├── index.html            # Entry HTML
├── src/
│   ├── main.tsx          # React entry point
│   ├── App.tsx           # Main app component
│   ├── types/api.ts      # Generated TypeScript types
│   └── services/         # API client and services
└── .gitignore            # Ignore node_modules, dist, etc.
```

**API Client Generation**:
- Creates services for each database table
- Implements retry logic with exponential backoff
- Uses axios with proper error handling
- Calls correct endpoints: `/db/query`, `/db/query/view`, `/db/data`

### 5. ApiGenerator (api_generator.py)
**Purpose**: Generates type-safe API clients and React hooks.

**Service Generation**:
- One service per database table
- CRUD operations using generated DTOs
- Proper TypeScript typing throughout
- Integrates with main API client for requests

**Hook Generation**:
- React hooks for common operations (useQuery, useMutation)
- Proper error handling and loading states
- TypeScript generics for type safety

### 6. FrontendCompiler (compiler.py)
**Purpose**: Validates generated frontend by running TypeScript compilation.

**Validation Process**:
- Runs `npm install` to install dependencies
- Executes `npm run build` to compile TypeScript
- Captures and reports compilation errors
- Returns success/failure with detailed error messages

### 7. Configuration (config.py)
**Pydantic BaseSettings**: Following Python library best practices.

**Environment Variables** (prefix: `AI_FRONTEND_`):
- `CLAUDE_CODE_DOCKER_IMAGE` - Docker image for Claude Code
- `MAX_ITERATIONS` - Maximum Claude Code iterations
- `TIMEOUT_SECONDS` - Claude Code operation timeout
- `RETRY_ATTEMPTS` - Number of retry attempts
- `API_BASE_URL` - Target API server URL
- Plus Material-UI, Vite, and TypeScript settings

## File Organization

### Source Structure
```
src/ai_frontend/
├── __init__.py           # Public API exports
├── core.py               # Main AiFrontend class
├── config.py             # Configuration with BaseSettings
├── claude_integration.py # Docker-based Claude Code execution
├── skeleton_generator.py # React project scaffolding
├── api_generator.py      # API client generation
├── type_generator.py     # TypeScript type generation
├── compiler.py           # Frontend validation
├── exceptions.py         # Custom exception types
└── utils.py              # Utility functions
```

### Generated Frontend Structure
```
frontend/
├── schema.yaml           # Copy of database schema
├── package.json          # Node.js dependencies
├── vite.config.ts        # Build configuration
├── tsconfig.json         # TypeScript settings
├── index.html            # Entry point
├── src/
│   ├── main.tsx          # React app entry
│   ├── App.tsx           # Generated main component
│   ├── types/api.ts      # Generated TypeScript types
│   └── services/         # Generated API services
├── dist/                 # Compiled output (gitignored)
├── node_modules/         # Dependencies (gitignored)
├── SEMANTIC_DOCS.md      # Claude-generated documentation
└── .gitignore            # Ignore patterns
```

## Integration Patterns

### Transaction Usage Pattern
```python
# Typical usage in host application
async with git_layer.begin_transaction() as transaction:
    frontend = AiFrontend(config)
    
    result = await frontend.generate_frontend(
        request="Create a user management interface",
        schema=db_schema,
        transaction=transaction,
        project_name="user-portal"
    )
    
    if result.success:
        # Transaction commits automatically
        print(f"Frontend generated at: {result.output_path}")
    else:
        # Transaction rolls back automatically
        print(f"Generation failed: {result.error}")
```

### Schema Synchronization Pattern
```python
# When database schema changes
async with git_layer.begin_transaction() as transaction:
    # Get updated schema from ai-db
    new_schema = await ai_db.get_schema(transaction)
    
    # Update frontend to match new schema
    result = await frontend.update_frontend(
        request="Update interface for new user.avatar field",
        schema=new_schema,
        transaction=transaction
    )
```

### Seed Data Pattern
```python
# Initialize from existing React project
async with git_layer.begin_transaction() as transaction:
    await frontend.init_from_folder(
        source_path=Path("./my-existing-frontend"),
        transaction=transaction
    )
    # Validates TypeScript compilation before committing
```

## Testing Strategy

### Unit Test Coverage
- **31 tests** covering all major functionality
- **Mock transactions** for git-layer independence
- **AI API mocking** for deterministic testing
- **Async/await patterns** throughout

### Test Categories
1. **Core functionality** (test_core.py) - Main AiFrontend class
2. **Configuration** (test_config.py) - BaseSettings validation
3. **Type generation** (test_type_generator.py) - Schema to TypeScript
4. **Utilities** (test_utils.py) - Helper functions

### Testing Without Git
- Uses plain folder paths instead of git transactions
- Validates library independence from git-layer
- Enables fast unit testing

## Docker Integration

### Claude Code Execution
```bash
docker run --rm \
  -v "$(pwd)/frontend:/workspace" \
  -v "$(pwd)/prompt.md:/prompt.md:ro" \
  -w /workspace \
  --env ANTHROPIC_API_KEY \
  anthropics/claude-code:latest \
  claude /prompt.md --no-interactive
```

### Security Considerations
- Read-only mount for prompt file
- Working directory isolated in container
- API key passed through environment only
- Automatic container cleanup after execution

## Error Handling Details

### Exception Flow
1. **Validation Errors**: Immediately raised (fail-fast)
2. **Claude Code Failures**: Retried with exponential backoff
3. **Compilation Errors**: Captured and returned in result
4. **Git Integration**: Always notifies transaction of outcomes

### Error Message Format
- **User-facing**: Friendly description of what went wrong
- **Technical details**: Full error context in logs
- **Actionable guidance**: What the user should do next

### Recovery Patterns
- **Retry logic**: Configurable attempts for transient failures
- **Iteration support**: Multiple Claude Code attempts for complex requests
- **Compilation feedback**: Provides errors to Claude for fixing

## Performance Considerations

### Async Operations
- All I/O operations use async/await
- Parallel execution where possible
- Proper timeout handling

### Resource Management
- Docker containers auto-cleanup
- Temporary files managed by git-layer
- Memory-efficient schema processing

### Caching Strategy
- No caching in POC (per requirements)
- Generated types cached in frontend folder
- Schema stored locally for reference

## Future Extension Points

### Chat Integration
- Configuration ready for ai-hub chat features
- Context files pattern supports conversation history
- Error messages suitable for AI interpretation

### Multiple Frontends
- Library supports multiple project names
- Can generate different frontends for same schema
- Repository structure supports multiple frontend folders

### Custom Templates
- Skeleton generator easily extendable
- Template system for different UI frameworks
- Component pattern recognition for reuse

### Advanced TypeScript
- Generic type support for complex schemas
- Validation integration with JSON Schema
- Runtime type checking capabilities

## Troubleshooting Guide

### Common Issues

**Generation Timeout**:
- Increase `timeout_seconds` in configuration
- Check Docker daemon availability
- Verify ANTHROPIC_API_KEY is valid

**Compilation Failures**:
- Check generated TypeScript syntax
- Verify schema format compliance
- Review Claude Code error messages in logs

**Transaction Failures**:
- Ensure write escalation called before modifications
- Check git repository permissions
- Verify transaction context validity

**Schema Mismatches**:
- Validate JSON Schema format
- Check for unsupported field types
- Ensure schema compatibility with TypeScript

### Debugging Tools

**Verbose Logging**:
```python
config = AiFrontendConfig(log_level="DEBUG")
```

**Preserve Failed Branches**:
- Git-layer automatically creates failure branches
- Inspect `failed-transaction-*` branches for debugging
- SEMANTIC_DOCS.md contains Claude's reasoning

**Manual Validation**:
```bash
cd frontend/
npm install
npm run build  # Check TypeScript compilation
npm run dev    # Start development server
```

## Code Quality Standards

### CLAUDE.md Compliance
- **No defensive programming**: Trust type system
- **Exception propagation**: Let errors bubble up naturally
- **Explicit typing**: Type annotations everywhere
- **No optional parameters**: Explicit parameter requirements

### Best Practices Followed
- **Dependency injection**: Ready for future DI container
- **Configuration management**: Pydantic BaseSettings
- **Error handling**: Boundary layer exception management
- **Testing**: Behavior-focused, not implementation-focused

This documentation should enable future maintainer agents to understand, extend, and debug the ai-frontend implementation effectively.