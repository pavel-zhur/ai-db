# Git-Layer Phase 1 Inconsistencies Report

After reviewing all project documentation, here are the inconsistencies and integration issues discovered:

## 1. Transaction Context Interface Mismatch

### Expected by Other Components
All components expect a `TransactionContext` object with these attributes:
```python
class TransactionContext:
    transaction_id: str
    working_directory: str
    is_write_escalated: bool
    
    def escalate_write(self) -> str:
        """Returns new working directory for writes"""
```

### What Git-Layer Provides
Git-Layer provides a `Transaction` object with different interface:
```python
class Transaction:
    transaction_id: str  # ✓ Matches
    path: str  # ❌ Different name (expected: working_directory)
    # ❌ Missing: is_write_escalated property
    
    def write_escalation_required(self) -> None:  # ❌ Different name and signature
        """Escalates but returns None"""
```

**Impact**: Other components won't be able to use git-layer without adapter code.

## 2. Transaction Creation API Mismatch

### Expected by AI-DB
AI-DB documentation mentions expecting git-layer transaction as parameter:
```python
async def execute(query: str, permissions: PermissionLevel, 
                 transaction: TransactionContext, context: Optional[QueryContext] = None)
```

### What Git-Layer Provides
Git-Layer uses context manager pattern:
```python
with git_layer.begin("/path/to/repo", message="...") as transaction:
    # Use transaction
```

**Impact**: AI-DB expects to receive a transaction object, but git-layer requires wrapping all operations in a context manager.

## 3. Async/Sync Mismatch

### Other Components
- AI-DB: Fully async (`async def execute`)
- AI-Frontend: Fully async (`async def generate_frontend`)
- Console: Fully async
- MCP: Async tool handlers

### Git-Layer
- Completely synchronous
- No async support

**Impact**: Async components will need to use `asyncio.to_thread()` or similar to call git-layer.

## 4. Write Escalation Behavior

### Expected Behavior (from other docs)
- `escalate_write()` returns new working directory
- Can check `is_write_escalated` status
- Escalation happens automatically when needed

### Git-Layer Behavior
- Must explicitly call `write_escalation_required()`
- No return value from escalation
- No way to check escalation status
- Manual escalation only

**Impact**: Components expecting automatic escalation will fail.

## 5. Missing Expected Methods

### AI-DB Expects
AI-DB technical Q&A mentions git-layer should provide:
- Location/folder updates when escalation happens
- Interface to notify about write operations

### Git-Layer Missing
- No callback or notification mechanism for folder changes
- No way to query transaction state

## 6. Operation Commit Confusion

### AI-DB Understanding
From technical Q&A: "every successful operation inside a non-committed transaction should be a commit to a branch"

### Git-Layer Implementation
- Provides `operation_complete(message)` for this purpose
- But this isn't documented in expected interface
- Other components don't know to call this

**Impact**: Operations might not be committed as expected.

## 7. Error Handling Inconsistency

### Expected (from AI-DB)
- Git-layer manages file operations transparently
- Errors during operations should be handled by git-layer

### Git-Layer Reality
- Only handles Git operations
- File I/O errors propagate directly
- No special error handling for file operations

## 8. Repository Path Management

### Console Implementation
Console creates transactions with a fixed repository path from config.

### Git-Layer Requirement
Requires repository path for every `begin()` call.

**Note**: This actually works fine, just different than expected.

## 9. Transaction Lifecycle Ambiguity

### MCP Server Expectation
MCP server has separate tools for begin/commit/rollback, suggesting explicit transaction management.

### Git-Layer Design
Transactions are context managers that auto-commit/rollback.

**Impact**: MCP server tools don't align with git-layer design.

## 10. Missing Recovery Mechanism Documentation

### Issue
None of the other components mention how to handle repository corruption or recovery.

### Git-Layer Provides
`git_layer.recover(repo_path)` function, but other components don't know about it.

## Recommendations for Supervisor

1. **Create Adapter Layer**: Build a `TransactionContext` wrapper around git-layer's `Transaction` to match expected interface.

2. **Add Async Wrapper**: Create async wrapper functions for git-layer operations.

3. **Standardize Write Escalation**: Either:
   - Update git-layer to auto-escalate on first write
   - Update other components to explicitly call escalation

4. **Document Integration Points**: Create integration guide showing exact usage patterns.

5. **Align MCP Tools**: Either:
   - Redesign MCP tools to work with context managers
   - Add transaction state management to MCP server

6. **Add State Properties**: Enhance git-layer Transaction with:
   - `is_write_escalated` property
   - `working_directory` alias for `path`

7. **Clarify Operation Commits**: Ensure all components know when/how to call `operation_complete()`.

## Critical Integration Blockers

1. **Interface mismatch** between expected `TransactionContext` and provided `Transaction`
2. **Async/sync impedance** requiring wrapper code
3. **Write escalation API** differences
4. **Missing state query methods**

These must be resolved before components can integrate successfully.