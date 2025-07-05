# Phase 1 Inconsistencies Report - MCP Servers

## Overview

This document identifies inconsistencies discovered between the MCP server implementation and the other four services (AI-DB, AI-Frontend, Git-Layer, Console) after reviewing all Phase 1 implementation documentation and README files. This report includes unresolved questions from the MCP implementation and critical information needed to make all components work together in production.

## Critical Inconsistencies

### 1. Transaction Context Interface Mismatch

**Issue**: The transaction context interfaces don't match between implementations.

**MCP Expected** (from protocols.py):
```python
class TransactionContext(Protocol):
    transaction_id: str
    working_directory: str
    async def write_escalation(self) -> str
```

**AI-DB Implementation** (from phase-1-implementation.md):
```python
class TransactionContext:
    transaction_id: str
    working_directory: str
    is_write_escalated: bool
    def escalate_write(self) -> str  # Different method name, sync not async
```

**Git-Layer Implementation** (from README.md and phase-1-implementation.md):
```python
# Context manager based:
with git_layer.begin("/path/to/repo", message="Update data") as transaction:
    transaction.write_escalation_required()  # Different method name
    transaction.path  # Not working_directory
    transaction.operation_complete(message)  # Not in MCP protocol
```

**Additional Issues**:
- Git-Layer is **synchronous**, MCP expects **async**
- Git-Layer uses context managers, not individual transaction methods
- No `TransactionContext` class exported, only internal implementation
- `write_escalation_required()` doesn't return new directory, updates internal state

**Impact**: MCP server transaction tools are completely incompatible with Git-Layer's API.

### 2. AI-DB API Method Signatures

**Issue**: Method signatures differ between MCP expectations and AI-DB implementation.

**MCP Expected**:
```python
async def execute(query: str, permission_level: PermissionLevel, transaction_context: Optional[Any])
```

**AI-DB Actual** (from API.md):
```python
async def execute(query: str, permissions: PermissionLevel, transaction: TransactionContext, context: Optional[QueryContext] = None)
```

**Differences**:
- Parameter name: `permission_level` vs `permissions`
- Parameter name: `transaction_context` vs `transaction`
- Missing `QueryContext` parameter in MCP
- Transaction is not optional in AI-DB

**Impact**: MCP tools will fail to call AI-DB methods correctly.

### 3. Query Result Structure

**Issue**: Return type structures don't align.

**MCP Expected** (AIDBQueryResult in protocols.py):
```python
@dataclass
class AIDBQueryResult:
    status: str
    data: Optional[list[dict[str, Any]]]
    schema: Optional[dict[str, Any]]
    data_loss_indicator: DataLossIndicator
    ai_comment: str = ""
    compiled_plan: Optional[str] = None
    error: Optional[str] = None
```

**AI-DB Actual** (QueryResult from API.md):
```python
@dataclass
class QueryResult:
    status: bool  # Boolean, not string!
    data: Optional[List[Dict[str, Any]]]
    schema: Optional[Dict[str, Any]]
    data_loss_indicator: DataLossIndicator
    ai_comment: Optional[str]  # Optional, not default empty string
    compiled_plan: Optional[str]
    transaction_id: Optional[str]  # Extra field
    error: Optional[str]
    execution_time: Optional[float]  # Extra field
```

**Impact**: Result parsing will fail due to type mismatches.

### 4. AI-Frontend Interface Discrepancies

**Issue**: AI-Frontend method signatures don't match MCP expectations.

**MCP Expected**:
```python
async def generate(request: str, transaction_context: Optional[Any]) -> AIFrontendResult
```

**AI-Frontend Actual** (from api-reference.md):
```python
async def generate_frontend(request: str, schema: Dict[str, Any], transaction_context: TransactionContext, project_name: str = "ai-frontend") -> GenerationResult
```

**Differences**:
- Method name: `generate` vs `generate_frontend`
- Missing required `schema` parameter in MCP
- Missing optional `project_name` parameter
- Return type: `AIFrontendResult` vs `GenerationResult`
- Transaction context is required, not optional

**Impact**: MCP cannot call AI-Frontend without schema information.

### 5. Git-Layer Transaction API

**Issue**: Git-Layer uses different API than expected by MCP.

**MCP Expected**:
```python
async def begin_transaction() -> str
async def commit_transaction(transaction_id: str, commit_message: str) -> None
async def rollback_transaction(transaction_id: str) -> None
```

**Git-Layer Actual** (from README.md and phase-1-implementation.md):
```python
# Context manager based, not individual methods
with git_layer.begin("/path/to/repo", message="Update data") as transaction:
    # No separate transaction ID management
```

**Impact**: MCP transaction tools won't work with Git-Layer's context manager approach.

### 6. Async vs Sync Mismatch

**Issue**: Some operations are async in MCP but sync in implementations.

- Git-Layer is entirely synchronous (no async support mentioned)
- AI-DB's `TransactionContext.escalate_write()` is sync, MCP expects async
- Console expects async operations but Git-Layer provides sync

**Impact**: Async/await incompatibility will cause runtime errors.

## Minor Inconsistencies

### 1. Module Import Paths

**MCP Assumes**:
```python
from ai_db import AIDB
from ai_frontend import AIFrontend
from git_layer import GitLayer
```

**Actual** (varies by project):
- AI-DB: `from ai_db import AIDB, PermissionLevel` ✓
- AI-Frontend: `from ai_frontend import AiFrontend` (different casing!)
- Git-Layer: `import git_layer` (module-level functions, no class)

### 2. Configuration Differences

**MCP Server Config**:
- Uses environment variables like `AI_DB_USE_MOCKS`
- Expects paths like `/workspace/data` and `/workspace/frontend`

**Other Services**:
- AI-DB uses `AI_DB_API_BASE`, `AI_DB_API_KEY`, etc.
- AI-Frontend uses `AiFrontendConfig` dataclass
- Git-Layer takes repo path as parameter
- Console uses YAML config files

### 3. Error Types

**MCP Defines**: Generic error handling with string messages

**Services Define**:
- AI-DB: Specific exceptions (AIDBError, PermissionError, etc.)
- AI-Frontend: Specific exceptions (AiFrontendError, ClaudeCodeError, etc.)
- Git-Layer: GitOperationError, TransactionError

**Impact**: MCP loses error type information, only passing strings.

### 4. Schema Format Assumptions

**MCP Assumes**: Schema is a simple dictionary

**AI-Frontend Expects**: Specific schema structure with tables/views/columns

**AI-DB Provides**: Schema objects with methods, not just dictionaries

### 5. Missing Context Information

**MCP Missing**:
- No way to pass `QueryContext` to AI-DB (includes retry info)
- No way to get current schema before calling AI-Frontend
- No session/conversation context management

## Recommendations for Resolution

### 1. Update Protocol Interfaces
- Fix `TransactionContext` to match Git-Layer's actual API
- Add missing parameters to method signatures
- Correct return types to match implementations

### 2. Add Adapter Layer
- Create adapter classes to bridge interface differences
- Handle sync/async conversions
- Map between different parameter names

### 3. Schema Management
- Add tool to fetch schema before frontend generation
- Pass schema as part of frontend generation request
- Cache schema for performance

### 4. Transaction Handling
- Redesign transaction tools to work with Git-Layer's context manager
- Consider maintaining transaction context in MCP server
- Handle write escalation differences

### 5. Error Handling
- Preserve error types through MCP protocol
- Add error type information to responses
- Map specific exceptions to MCP error categories

### 6. Configuration Alignment
- Standardize environment variable names
- Create configuration mapping layer
- Document all required settings

## Impact Assessment

**High Impact**:
1. Transaction interface mismatch - blocks all operations
2. Method signature differences - prevents basic functionality
3. Async/sync incompatibility - causes runtime failures

**Medium Impact**:
4. Schema passing for AI-Frontend - limits frontend generation
5. Error type information loss - complicates debugging
6. Result type mismatches - requires data transformation

**Low Impact**:
7. Import path differences - easy to fix
8. Configuration differences - can be mapped
9. Minor naming inconsistencies - cosmetic issues

## MCP Implementation Unresolved Questions

These questions from the MCP implementation need answers for production readiness:

1. **Transaction Context Structure**: What exactly should be passed as transaction_context? The implementations show different structures.

2. **Compiled Query Plan Format**: AI-DB uses base64-encoded pickles, but this wasn't documented initially.

3. **Schema Format**: AI-DB provides Schema objects with methods, not just dictionaries as MCP assumed.

4. **Error Recovery**: Should MCP handle transaction rollback on AI-DB errors, or does Git-Layer handle this?

5. **Progress Reporting**: Long operations like frontend generation could benefit from MCP progress tokens.

6. **Frontend Generation Context**: AI-Frontend requires schema, but MCP has no way to fetch current schema before generation.

7. **API Server Assumption**: AI-Frontend expects an API server for generated frontends to call - where is this implemented?

8. **Chrome MCP Integration**: How does this work with AI-Frontend? Not documented clearly.

## Critical Integration Requirements

### 1. Async/Sync Bridge
Git-Layer is synchronous but all other components expect async operations. Need to:
- Wrap Git-Layer calls in `asyncio.run_in_executor()`
- Or make Git-Layer async-compatible
- Or make transaction operations synchronous throughout

### 2. Transaction Lifecycle Management
Current incompatibility between Git-Layer's context manager and MCP's individual transaction methods requires:
- MCP to maintain transaction contexts internally
- Map transaction IDs to active Git-Layer contexts
- Handle context manager lifecycle across multiple MCP tool calls

### 3. Schema Passing for Frontend Generation
AI-Frontend requires schema but MCP tool doesn't have it:
- Need to call AI-DB's get_schema first
- Pass schema as part of generate_frontend request
- Or have AI-Frontend fetch schema directly (but how without transaction context?)

### 4. Import Path Standardization
```python
# Current inconsistencies:
from ai_db import AIDB  # Correct
from ai_frontend import AiFrontend  # Note: lowercase 'i'
import git_layer  # Module functions, not class
```

### 5. Missing API Server
AI-Frontend generates code expecting these endpoints:
- `POST /api/query` - For SELECT queries
- `POST /api/execute` - For mutations

**No component implements this API server!** Options:
1. Add API server to Console
2. Create separate API server component
3. Modify AI-Frontend to generate direct AI-DB calls

## Configuration Alignment Issues

### Environment Variables
Different naming conventions across services:
- MCP: `AI_DB_USE_MOCKS`, `AI_DB_GIT_REPO_PATH`
- AI-DB: `AI_DB_API_KEY`, `AI_DB_API_BASE`, `AI_DB_MODEL`
- Console: Uses YAML config files primarily
- No standard configuration approach

### Path Configurations
- MCP defaults: `/workspace/data`, `/workspace/frontend`
- Git-Layer: Requires explicit path, no defaults
- Console: `./data` as default
- Need agreement on default paths

## Production Readiness Blockers

1. **No Working Transaction System**: Git-Layer interface completely incompatible with MCP expectations
2. **No API Server**: Frontend generation creates non-functional code without API backend
3. **Async/Sync Mismatch**: Will cause runtime failures
4. **Missing Schema Context**: Frontend generation will fail without schema
5. **No Error Type Preservation**: MCP loses all error type information

## Recommended Solutions

### 1. Create Adapter Layer (Immediate)
```python
class GitLayerAdapter:
    """Adapts Git-Layer's sync context manager to MCP's async interface"""
    def __init__(self, repo_path: str):
        self._repo_path = repo_path
        self._transactions = {}
    
    async def begin_transaction(self) -> str:
        # Create transaction in thread pool
        # Store context manager
        # Return transaction ID
    
    async def commit_transaction(self, tx_id: str, message: str) -> None:
        # Exit context manager successfully
    
    async def rollback_transaction(self, tx_id: str) -> None:
        # Exit context manager with exception
```

### 2. Add Schema Tool (Immediate)
Before any frontend generation, MCP must:
1. Call get_schema tool
2. Pass schema to generate_frontend request
3. Update protocol to include schema parameter

### 3. Implement API Server (Short-term)
Either:
- Add to Console as integrated server
- Create new `api-server` component
- Document clearly where this should run

### 4. Standardize Interfaces (Medium-term)
All services should agree on:
- Method names and signatures
- Parameter names
- Return types
- Async vs sync operations

## Information for Supervisor Agent

### Critical Decisions Needed:

1. **API Server Location**: Where should the API server that AI-Frontend expects be implemented?

2. **Transaction Model**: Should we adapt to Git-Layer's context manager model or change Git-Layer to support individual transaction methods?

3. **Async Strategy**: Make everything async or add sync/async adapters?

4. **Configuration Management**: Standardize on environment variables, YAML files, or both?

5. **Default Paths**: Agree on standard default paths for data and frontend directories

### Integration Test Requirements:

To ensure production readiness, we need integration tests that:
1. Start Git-Layer transaction
2. Use AI-DB to create schema and data
3. Use AI-Frontend to generate UI
4. Verify generated UI can call API endpoints
5. Commit transaction successfully

Currently, no such integration tests exist.

## Next Steps

1. **Immediate**: 
   - Fix protocol interfaces to match actual implementations
   - Create Git-Layer adapter for async compatibility
   - Add schema parameter to frontend generation

2. **Short-term**: 
   - Implement API server (decide where)
   - Standardize configuration approach
   - Create integration tests

3. **Medium-term**: 
   - Align all interfaces across services
   - Add progress reporting for long operations
   - Implement proper error type preservation

4. **Long-term**: 
   - Create integration test suite
   - Add monitoring and metrics
   - Document deployment architecture