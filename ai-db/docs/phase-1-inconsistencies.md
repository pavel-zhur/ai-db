# AI-DB Phase 1 Inconsistencies Report

After reviewing all phase-1-implementation.md files from all five projects, here are the critical inconsistencies and integration issues that need resolution for production-ready integration:

## 1. Critical Transaction Context Mismatch

### Issue
AI-DB and Git-Layer have incompatible transaction interfaces:

**AI-DB expects:**
```python
class TransactionContext:
    transaction_id: str
    working_directory: str  # Property name
    is_write_escalated: bool
    def escalate_write(self) -> str  # Method name and signature
```

**Git-Layer actually provides:**
```python
class Transaction:
    id: str  # Different property name
    path: str  # Different property name
    def write_escalation_required(self) -> None  # Different method name, no return
    def operation_complete(message: str) -> None  # AI-DB doesn't know about this
```

### AI-DB Impact
- My code uses `transaction_context.working_directory` but should use `transaction.path`
- My code calls `escalate_write()` but should call `write_escalation_required()`
- I never call `operation_complete()` which Git-Layer expects for proper commits

### Resolution Required
Must update AI-DB to match Git-Layer's actual interface or create an adapter.

## 2. Missing get_schema() Method

### Issue
MCP Server expects AI-DB to have:
```python
async def get_schema(include_semantic_docs: bool) -> dict[str, Any]
```

But AI-DB doesn't implement this method at all.

### Resolution Required
Add `get_schema()` method to AIDB class that returns current schema in expected format.

## 3. Async/Sync Impedance Mismatch

### Issue
- **AI-DB**: Fully async (`async def execute()`)
- **Git-Layer**: Fully synchronous (no async support)
- **Console**: Has to bridge this gap somehow
- **MCP**: Expects Git-Layer to be async but it's not

### Current Problem
AI-DB can't properly use Git-Layer without blocking the event loop.

### Resolution Required
Either:
- Add async wrapper around Git-Layer operations
- Use `asyncio.to_thread()` for Git operations
- Make Git-Layer async (major change)

## 4. Schema Format Incompatibility

### Issue
AI-DB and AI-Frontend expect completely different schema formats:

**AI-DB stores (YAML):**
```yaml
name: users
columns:
  - name: id
    type: integer
    nullable: false
constraints:
  - name: pk_users
    type: primary_key
    columns: [id]
```

**AI-Frontend expects (JSON):**
```json
{
  "tables": {
    "users": {
      "columns": {
        "id": {
          "type": "integer",
          "nullable": false,
          "primary_key": true
        }
      }
    }
  }
}
```

### Resolution Required
Need schema transformation layer or standardize on one format.

## 5. Missing HTTP API Layer

### Issue
AI-Frontend assumes AI-DB exposes HTTP endpoints:
- `POST /api/query`
- `POST /api/execute`

But AI-DB is just a library with no HTTP server.

### Resolution Required
Either:
- Add HTTP API server to AI-DB
- Update AI-Frontend to work differently
- Create separate API gateway service

## 6. Permission Level Case Sensitivity

### Issue
- AI-DB uses lowercase: `PermissionLevel.SELECT.value = "select"`
- MCP infers from SQL patterns and might use different casing
- Console's comments show uppercase but code uses lowercase

### Resolution Required
Document exact permission strings and ensure consistency.

## 7. operation_complete() Never Called

### Issue
Git-Layer expects `operation_complete(message)` to be called after each operation for proper commit tracking, but:
- AI-DB never calls it
- Console doesn't know about it
- MCP doesn't mention it

### Resolution Required
Update AI-DB to call `operation_complete()` after each file operation.

## 8. Compiled Query Format Undefined

### Issue
- AI-DB returns base64-encoded pickled Python bytecode
- MCP asks "what format do compiled query plans use?"
- Console mentions storing compiled plans but doesn't specify format

### Security Concern
Pickled objects can be security risk if shared between services.

### Resolution Required
Define safe serialization format for compiled queries.

## 9. Property Name Mismatches

### Issue
Multiple property name inconsistencies:
- `working_directory` vs `path`
- `transaction_id` vs `id`
- `transaction_context` vs `transaction`

### Resolution Required
Standardize all property names across services.

## 10. Error Handling Strategy

### Issue
- AI-DB returns `QueryResult` with `status: bool` and `error: Optional[str]`
- Git-Layer raises exceptions
- Console expects to catch exceptions from AI-DB
- MCP returns TextContent with `isError: true`

### Resolution Required
Decide on consistent error handling approach.

## AI-DB Specific Unresolved Questions

From my implementation, these questions remain unanswered:

1. **Large Tables**: Current implementation loads everything into memory. How should we handle tables with millions of rows?

2. **Concurrent Access**: What happens if multiple transactions try to access the same data? I assumed git-layer handles this, but Git-Layer docs say it's single-threaded only.

3. **Schema Evolution**: How are schema migrations tracked over time? Currently only current state is maintained.

4. **Security**: How much should we trust AI-generated code? Using RestrictedPython but may need more validation.

5. **View Dependencies**: How to handle views that depend on other views? Not currently tracked.

6. **Claude Code Discovery**: AI-Frontend assumes Claude Code CLI is in PATH, but how do we validate this?

7. **Transaction ID Generation**: Who generates transaction IDs? Git-Layer seems to but it's not clear.

8. **Schema Caching**: Should AI-DB cache schemas for performance? Console asks the same question.

## Critical Integration Gaps

1. **No Schema Synchronization**: How does AI-Frontend get the current schema? Through files or API?

2. **Transaction Lifecycle**: Who controls transaction lifecycle? Console? MCP? The user?

3. **Configuration Conflicts**: Each service has different config approaches and env var names.

4. **No Integration Tests**: No service has integration tests with others.

## Recommendations for Production Readiness

### Immediate Actions Required

1. **Create Adapter Layer**: Build `GitLayerTransactionAdapter` that converts between AI-DB's expected interface and Git-Layer's actual interface.

2. **Add Missing Methods**: 
   - Add `get_schema()` to AIDB class
   - Add calls to `operation_complete()` in storage layer

3. **Standardize Interfaces**: Create shared interface definitions that all services import.

4. **Fix Async/Sync**: Use `asyncio.to_thread()` for Git-Layer operations in AI-DB.

5. **Define Schema Format**: Pick one canonical format and add transformers.

### Code Changes Needed in AI-DB

1. Update `TransactionContext` usage to match Git-Layer
2. Add `get_schema()` method
3. Call `operation_complete()` after file writes
4. Fix async/sync bridging for Git operations
5. Add schema format transformer
6. Consider adding HTTP API server component

### Documentation Needed

1. Canonical interface specifications
2. Schema format specification
3. Permission level strings
4. Error handling patterns
5. Configuration standards
6. Integration test scenarios

## Summary

The current implementations have significant interface mismatches that prevent them from working together. The most critical issues are:

1. Transaction context interface mismatch
2. Missing get_schema() method
3. Async/sync incompatibility
4. Schema format differences
5. Missing HTTP API layer

These must be resolved before the system can function as an integrated whole.