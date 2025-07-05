# Phase 1 Inconsistencies Report - MCP Servers

## Overview

This document identifies inconsistencies discovered between the MCP server implementation and the other four services (AI-DB, AI-Frontend, Git-Layer, Console) after reviewing their Phase 1 implementation documentation.

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

**Git-Layer Implementation** (from README.md):
```python
transaction.write_escalation_required()  # Different API
transaction.path  # Not working_directory
transaction.operation_complete(message)  # Not in MCP protocol
```

**Impact**: MCP server will fail to call correct methods on transaction objects.

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

## Next Steps

1. **Immediate**: Fix protocol interfaces to match actual implementations
2. **Short-term**: Add adapter layer for interface compatibility
3. **Medium-term**: Standardize APIs across all services
4. **Long-term**: Create integration tests to prevent future drift