# AI-DB Phase 1 Implementation Details

## Overview

AI-DB is a fully functional AI-native database engine that interprets queries in natural language or any programming language. It uses LangChain with OpenAI-compatible models as the core query interpretation engine.

## Architecture

### Core Components

1. **AI Agent (`core/ai_agent.py`)**
   - Uses LangChain with OpenAI-compatible API
   - Two-phase processing: analyze query → generate execution plan
   - Handles validation errors with retry logic (max 3 retries by default)
   - Generates Python code for SELECT queries and views

2. **Engine (`core/engine.py`)**
   - Main orchestrator using dependency injection pattern
   - Routes operations to appropriate handlers based on type
   - Manages transaction context throughout execution
   - Returns typed `QueryResult` objects

3. **Storage Layer (`storage/`)**
   - `YAMLStore`: Handles raw YAML file operations
   - `SchemaStore`: Manages table schemas and semantic documentation
   - `ViewStore`: Persists compiled views as Python files
   - All writes trigger transaction escalation via git-layer

4. **Validation System (`validation/`)**
   - `DataValidator`: JSON Schema-based data validation
   - `ConstraintChecker`: Validates all constraint types
   - `SafeExecutor`: RestrictedPython sandbox for constraint execution

5. **Query Compiler (`core/query_compiler.py`)**
   - Compiles SELECT queries to pure Python functions
   - Uses RestrictedPython for safe execution
   - Serializes compiled queries as base64-encoded pickles
   - Provides utility functions for grouping, aggregation, joins

## Key Design Decisions

### AI Integration
- **LangChain Agent**: Simple, stateless agent without complex chains
- **Structured Output**: Uses Pydantic models with JsonOutputParser
- **Context Management**: Passes schema, semantic docs, and recent errors to AI
- **Error Recovery**: AI attempts to fix validation errors automatically

### Storage Format
```
data/
├── schemas/
│   └── {table_name}.schema.yaml      # Table definitions
├── tables/
│   └── {table_name}.yaml             # Table data
├── views/
│   ├── {view_name}.py                # Compiled view code
│   └── {view_name}.meta.yaml         # View metadata
├── constraints/
│   └── validators.py                 # Constraint functions (if needed)
└── documentation/
    └── semantic_meanings.yaml        # AI-generated documentation
```

### Transaction Integration
- Requires `TransactionContext` from git-layer for all operations
- Read operations work on current directory
- Write operations trigger `escalate_write()` for copy-on-write semantics
- Single-threaded assumption - no concurrency handling needed

### Permission Model
- `SELECT`: Read-only queries
- `DATA_MODIFY`: INSERT, UPDATE, DELETE
- `SCHEMA_MODIFY`: CREATE, ALTER, DROP tables
- `VIEW_MODIFY`: CREATE, DROP views

## Implementation Details

### Query Processing Flow
1. User submits query with permissions and transaction context
2. AI agent analyzes query and determines operation type
3. Permission check against requested operation
4. AI generates execution plan (file updates or Python code)
5. For SELECT: compile Python code and execute
6. For modifications: apply file updates and validate
7. On validation error: AI attempts to fix and retry
8. Return QueryResult with status, data, and metadata

### Constraint System
- **Primary Key**: Uniqueness and non-null validation
- **Foreign Key**: Referential integrity checks
- **Unique**: Multi-column uniqueness
- **Check**: Python expressions executed in sandbox
- **Not Null**: Simple null checks

All constraints are validated after data modifications but before persisting to disk.

### Query Compilation
- SELECT queries compile to Python functions
- Functions receive table data as dictionaries
- Support for filtering, joins, aggregations, grouping
- Compiled queries are serializable and reusable
- No external dependencies (pure Python only)

## Assumptions Made

1. **Git-layer Interface**: Assumed `TransactionContext` has `escalate_write()` method that returns new directory
2. **Single-threaded**: No concurrent access - git-layer handles isolation
3. **Small Data**: No optimization for large datasets - all data loads into memory
4. **AI Availability**: Assumes AI service is available and responsive
5. **Trust AI Output**: Limited validation of AI-generated code beyond syntax
6. **File System**: Direct file system access for all operations

## External Dependencies

### Required from git-layer:
```python
class TransactionContext:
    transaction_id: str
    working_directory: str
    is_write_escalated: bool
    
    def escalate_write(self) -> str:
        """Returns new working directory for writes"""
```

### Required Environment Variables:
- `AI_DB_API_KEY`: OpenAI-compatible API key (required)
- `AI_DB_API_BASE`: API endpoint (default: OpenAI)
- `AI_DB_MODEL`: Model name (default: gpt-4)

## Unresolved Questions

1. **Large Tables**: How should we handle tables with millions of rows? Current implementation loads everything into memory.

2. **Concurrent Access**: What happens if multiple transactions try to access the same data? Assumed git-layer handles this.

3. **Schema Evolution**: How are schema migrations tracked over time? Currently only current state is maintained.

4. **Performance Optimization**: Should we add indexing or caching? Currently no optimization beyond query compilation.

5. **Security**: How much should we trust AI-generated code? Currently using RestrictedPython but may need more validation.

6. **View Dependencies**: How to handle views that depend on other views? Not currently tracked.

## Integration Points

### For Console/MCP Server:
- Use `AIDB` class from `ai_db` module
- Always provide `TransactionContext` from git-layer
- Handle `QueryResult` objects appropriately
- Check `result.status` before using `result.data`

### For AI-Frontend:
- Schema information available via `QueryContext.schema`
- Compiled views stored as Python files in `views/` directory
- Schema changes may require frontend updates

### Example Integration:
```python
from ai_db import AIDB, PermissionLevel
from git_layer import GitTransaction

async def process_query(query: str, permission: str):
    async with GitTransaction() as txn:
        db = AIDB()
        result = await db.execute(
            query,
            PermissionLevel(permission),
            txn
        )
        if result.status:
            return result.data
        else:
            raise Exception(result.error)
```

## Testing

Comprehensive test suite includes:
- Unit tests for all components
- Integration tests for end-to-end scenarios
- Mock AI responses for deterministic testing
- Transaction escalation testing
- Constraint validation testing

Run tests with: `pytest tests/`

## Future Enhancements

1. **Savepoints**: Transaction savepoint support (placeholder exists)
2. **Indexes**: B-tree or hash indexes for performance
3. **Partitioning**: Table partitioning for large datasets
4. **Replication**: Read replicas for scaling
5. **Audit Trail**: Query history and change tracking
6. **Custom Functions**: User-defined functions in queries