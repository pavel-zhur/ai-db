# Phase 1 Inconsistencies Report - Console

## Overview

This document identifies inconsistencies found across the five parallel implementations (AI-DB, AI-Frontend, Git-Layer, MCP Server, and Console) that need to be resolved for proper system integration. Updated after reading all phase-1-implementation.md files.

## Critical Architectural Gaps

### 1. Missing AI-DB API Server Component

**Issue**: AI-Frontend expects an HTTP API server, but none exists.

**Details**:
- AI-Frontend's `api_generator.py` generates code calling `POST /api/query` and `POST /api/execute` endpoints
- AI-DB is implemented as a library (`AIDB` class), not an HTTP server
- MCP Server provides MCP protocol tools, not HTTP REST endpoints
- Console directly imports and uses AI-DB library

**Impact**: Generated frontends cannot communicate with AI-DB.

**Console's Current Approach**: Direct library usage, which works for console but not for frontends.

**Recommendation**: Need new "ai-db-api-server" component that:
```python
# Wraps AI-DB library in HTTP endpoints
POST /api/query -> AIDB.execute() with SELECT permission
POST /api/execute -> AIDB.execute() with appropriate permission
GET /api/schema -> AIDB.get_schema()
```

### 2. Git-Layer Async/Sync Confusion

**Issue**: Git-Layer is synchronous but all consumers expect async.

**Git-Layer Implementation**:
- All methods are synchronous
- Context manager uses `__enter__`/`__exit__` (not async versions)
- No async support mentioned in implementation

**Consumer Expectations**:
- Console uses `async with GitTransaction()` and `await transaction.__aenter__()`
- AI-DB is fully async and expects async transaction context
- MCP Server expects async transaction operations

**Impact**: Console's async usage of sync Git-Layer will fail at runtime.

**Recommendation**: Either:
1. Add async wrapper to Git-Layer, or
2. Update all consumers to use sync calls with `asyncio.run_in_executor()`

### 3. Transaction Context Interface Mismatch

**Issue**: Multiple incompatible transaction context interfaces.

**Git-Layer Provides**:
```python
class Transaction:
    @property
    def path(self) -> str  # Not "working_directory"
    def write_escalation_required(self)  # Not "escalate_write()"
    def operation_complete(message: str)
    def checkpoint(message: str)
```

**AI-DB Expects**:
```python
class TransactionContext:
    transaction_id: str
    working_directory: str  # Not "path"
    is_write_escalated: bool
    def escalate_write(self) -> str  # Not "write_escalation_required()"
```

**AI-Frontend Expects**:
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path  # Path type, not str
    commit_message_callback: Optional[callable]
```

**Console Currently Does**: Passes Git-Layer Transaction directly to AI-DB, which won't work.

**Recommendation**: Create adapter classes or standardize on actual Git-Layer interface.

### 4. Schema Format Incompatibility

**Issue**: AI-DB and AI-Frontend use completely different schema formats.

**AI-DB Actual Storage** (from implementation):
```yaml
# schemas/users.schema.yaml
name: users
description: User accounts table
columns:
  - name: id
    type: integer
    nullable: false
    primary_key: true
constraints:
  - type: primary_key
    columns: [id]
```

**AI-Frontend Expects** (JSON Schema format):
```json
{
  "tables": {
    "users": {
      "columns": {
        "id": {
          "type": "integer",
          "required": true,
          "primary_key": true
        }
      }
    }
  }
}
```

**Console's Problem**: When fetching schema for frontend generation, formats won't match.

**Recommendation**: AI-DB needs to provide a `get_schema()` method that returns JSON Schema format.

## Console-Specific Issues

### 1. Incorrect Transaction Usage

**Current Console Code**:
```python
self._git_transaction = GitTransaction(
    repo_path=self._config.git_layer.repo_path,
    message="Console transaction"
)
await self._git_transaction.__aenter__()  # WRONG - Git-Layer is sync
```

**Should Be** (if Git-Layer stays sync):
```python
self._git_transaction = git_layer.begin(
    repo_path=self._config.git_layer.repo_path,
    message="Console transaction"
)
self._git_transaction.__enter__()
```

### 2. Missing Transaction Adapter

**Issue**: Console passes Git-Layer transaction directly to AI-DB.

**Current**:
```python
result = await self._ai_db.execute(
    query=query,
    permissions=permissions,
    transaction=self._git_transaction  # Git-Layer Transaction
)
```

**Needed**: Adapter to convert Git-Layer Transaction to AI-DB's expected TransactionContext.

### 3. No operation_complete() Calls

**Issue**: Git-Layer expects `operation_complete()` after each operation, but Console never calls it.

**Git-Layer Design**: Each operation should create a commit in the transaction branch.

**Console Behavior**: Only commits at transaction end.

**Impact**: Loss of granular operation history.

### 4. Frontend Path Configuration

**Issue**: Console has no way to configure where frontends are served from.

**Current**: Reports `result.output_path` but doesn't handle serving.

**Needed**: Configuration for frontend deployment/serving strategy.

## Integration Gaps Found

### 1. Permission Inference Differences

**MCP Server**: Complex pattern matching to infer permissions
**Console**: Simple keyword-based detection
**Risk**: Same query might get different permissions

### 2. Error Handling Philosophy

**AI-DB**: 3 retries with AI attempting to fix errors
**AI-Frontend**: 5 iterations max
**Console**: No retry logic, just displays errors
**Git-Layer**: Preserves failed states in branches

### 3. Compiled Query Execution

**AI-DB**: Returns `compiled_plan` in results
**Console**: Mentions saving but doesn't implement storage
**MCP**: Has tool for executing compiled plans
**Gap**: No shared compiled plan storage mechanism

### 4. Environment Variable Conflicts

**Console Sets**:
- `AI_DB_API_BASE`
- `AI_DB_API_KEY` 
- `AI_DB_MODEL`

**AI-DB Expects**: Same variables (good)

**AI-Frontend Issue**: Needs API server URL but no env var defined

## My Unresolved Questions (Console)

1. **Async Git-Layer**: How do I properly integrate with synchronous Git-Layer in my async code?

2. **Transaction Adapter**: Should Console create the adapter between Git-Layer and AI-DB interfaces, or should this be in AI-DB?

3. **API Server**: Should Console be responsible for starting an AI-DB API server for frontends?

4. **Frontend Serving**: How should generated frontends be served to users?

5. **Compiled Plans**: Where should compiled query plans be stored for reuse?

6. **Schema Caching**: Should Console cache schemas between queries for performance?

7. **Progress Feedback**: How to show progress for long Claude Code operations?

8. **Export Formats**: Console supports CSV export but AI-DB returns Python objects - need conversion logic.

## Recommendations for Supervisor

### Immediate Fixes Needed

1. **Create AI-DB API Server**: New component to wrap AI-DB library
2. **Resolve Async/Sync**: Either make Git-Layer async or add sync support to consumers
3. **Standardize Interfaces**: Create canonical TransactionContext interface
4. **Fix Schema Format**: Add JSON Schema output to AI-DB
5. **Create Adapters**: Bridge components with different interfaces

### Console-Specific Actions

1. **Fix Git-Layer Integration**: Use proper sync calls or wait for async support
2. **Add Transaction Adapter**: Convert between Git-Layer and AI-DB interfaces  
3. **Implement operation_complete()**: Call after each database operation
4. **Add API Server Config**: For frontend communication
5. **Implement Compiled Plan Storage**: For query reuse

### System-Wide Needs

1. **Integration Tests**: Current unit tests don't catch interface mismatches
2. **Docker Compose**: For full system testing with all components
3. **Shared Type Definitions**: Common package with interfaces
4. **Configuration Schema**: Unified config for entire system
5. **Deployment Strategy**: How components discover each other

## Priority Order for Console

1. **Critical**: Fix async/sync Git-Layer usage (blocks everything)
2. **Critical**: Add transaction adapter (blocks AI-DB integration)
3. **High**: Support AI-DB API server config (blocks frontend testing)
4. **Medium**: Implement operation_complete() calls
5. **Low**: Add compiled plan storage
6. **Low**: Implement CSV export conversion

## Notes for Other Agents

- Console is the primary user interface - all user interactions flow through it
- Console maintains conversation history and session state
- Console handles output formatting for all query results
- Console provides transaction status visualization
- Console implements safety features (destructive operation confirmation)
- Console expects all components to be pip-installable