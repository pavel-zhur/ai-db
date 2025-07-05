# Git-Layer Phase 1 Inconsistencies Report (Updated)

After reviewing all five components' implementation files, here are the comprehensive inconsistencies and integration issues:

## 1. Critical Interface Mismatch: TransactionContext

### What Each Component Expects

**AI-DB Expects:**
```python
class TransactionContext:
    def escalate_write(self) -> str:
        """Returns new working directory after escalation"""
```

**AI-Frontend Expects:**
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path
    commit_message_callback: Optional[callable] = None
```

**MCP Servers Expect:**
- Separate operations: `begin_transaction()`, `commit_transaction(id, message)`, `rollback_transaction(id)`
- Transaction context passed as optional parameter to each operation

### What Git-Layer Actually Provides
```python
class Transaction:
    @property
    def path(self) -> str:  # ❌ Not "working_directory"
        """Working directory path"""
    
    @property
    def transaction_id(self) -> str:  # ✓ Matches AI-Frontend
        """Transaction ID"""
    
    def write_escalation_required(self) -> None:  # ❌ Different from escalate_write()
        """Signal writes will occur - returns None"""
    
    def operation_complete(self, message: str) -> None:  # ❌ Not expected by others
        """Commit after operation"""
    
    # ❌ Missing: commit_message_callback
    # ❌ Missing: way to check is_write_escalated
    # ❌ Context manager only - no separate begin/commit/rollback
```

**Impact**: No component can use git-layer without significant adapter code.

## 2. Async/Sync Incompatibility

### All Other Components
- AI-DB: `async def execute(...)`
- AI-Frontend: `async def generate_frontend(...)`
- Console: Fully async with asyncio
- MCP: All handlers are async

### Git-Layer
- Completely synchronous
- Context manager blocks until transaction completes

**Impact**: Every call to git-layer needs `await asyncio.to_thread()` wrapper.

## 3. Transaction Lifecycle Model Conflict

### MCP Server Design
MCP implemented separate tools expecting stateful transaction management:
```python
async def begin_transaction() -> str  # Returns transaction ID
async def commit_transaction(transaction_id: str, commit_message: str)
async def rollback_transaction(transaction_id: str)
```

### Git-Layer Design
Context manager pattern only:
```python
with git_layer.begin(repo_path, message) as txn:
    # All operations must happen here
    # Auto-commits on success, auto-rollbacks on exception
```

**Impact**: MCP transaction tools are incompatible with git-layer's design. Need complete redesign of either MCP tools or git-layer API.

## 4. Write Escalation Behavior Mismatch

### Expected by AI-DB
- Call `escalate_write()` and get new directory path
- Continue using returned path for operations

### Git-Layer Behavior
- Call `write_escalation_required()` (returns None)
- Continue using `transaction.path` (property changes internally)
- No way to know if escalation happened

**Impact**: AI-DB's execution flow is broken.

## 5. Missing Commit Message Callback

### AI-Frontend Requirement
AI-Frontend expects optional `commit_message_callback` in TransactionContext to generate meaningful commit messages during operations.

### Git-Layer
Only supports explicit `operation_complete(message)` calls.

**Impact**: AI-Frontend can't provide dynamic commit messages during Claude Code operations.

## 6. Repository Path Management Issues

### Console Implementation
Console passes repository path from config to all operations.

### MCP Implementation
MCP has no concept of repository path - expects it to be handled elsewhere.

### Git-Layer Requirement
Every `begin()` call needs explicit repository path.

**Impact**: MCP servers can't create transactions without additional configuration.

## 7. Permission Level Handling

### AI-DB Expectation
AI-DB receives `PermissionLevel` for every operation.

### Git-Layer
No concept of permissions - all operations are allowed within a transaction.

**Note**: This works fine, just means permission checking is purely in AI-DB.

## 8. Schema Evolution and Migration

### Unresolved Across All Components
- AI-DB mentions schema migrations but has no implementation
- AI-Frontend asks about handling schema changes for existing UIs
- Git-Layer only tracks current state
- No component handles schema versioning

**Impact**: Production deployments will break when schemas change.

## 9. Error Recovery Gaps

### Console Behavior
Console has retry logic and confirmation prompts.

### AI-DB Behavior
AI-DB has 3-retry limit for AI operations.

### Git-Layer Behavior
Git-Layer has `recover()` function but others don't know about it.

**Impact**: No coordinated error recovery strategy.

## 10. My (Git-Layer) Unresolved Questions

1. **Large Repository Performance**: How will temporary clones perform with large repos? No testing done.

2. **Network Filesystems**: Will Git operations work correctly on NFS/SMB/etc.? Unknown behavior.

3. **External Git Operations**: What happens if someone runs `git` commands while transaction is active? No protection.

4. **Resource Limits**: How many concurrent transactions before running out of disk space with clones? No limits implemented.

5. **Commit Message Coordination**: Should git-layer accept a callback for generating commit messages dynamically?

## Critical Production Blockers

### Must Fix Before Integration

1. **Interface Adapter Needed**: Create `TransactionContext` wrapper that:
   ```python
   class TransactionContextAdapter:
       def __init__(self, git_transaction: Transaction):
           self._txn = git_transaction
           self.transaction_id = git_transaction.transaction_id
           self.working_directory = Path(git_transaction.path)
       
       def escalate_write(self) -> str:
           self._txn.write_escalation_required()
           return str(self.working_directory)
   ```

2. **Async Wrapper Required**: Create async version:
   ```python
   async def begin_async(repo_path: str, message: str):
       return await asyncio.to_thread(git_layer.begin, repo_path, message)
   ```

3. **MCP Redesign**: Either:
   - Rewrite MCP to use context managers internally
   - Add state management to track active transactions
   - Or create transaction pool in MCP server

4. **Configuration Alignment**: Need unified configuration for:
   - Repository path
   - Git user settings  
   - Transaction timeout/limits

## Recommendations for Supervisor

### Immediate Actions

1. **Create Integration Layer**: Build adapters to bridge interface gaps between components.

2. **Standardize Interfaces**: Pick one transaction interface and update all components:
   - Option A: Update git-layer to match expected `TransactionContext`
   - Option B: Update all others to use git-layer's `Transaction`

3. **Async Strategy**: Either:
   - Make git-layer async (major rewrite)
   - Create official async wrappers
   - Document async usage patterns

4. **Schema Versioning**: Design and implement schema migration strategy across all components.

5. **Error Recovery Protocol**: Define how components should handle and recover from failures.

### Testing Requirements

1. **Integration Tests**: No component has tests for integration with others.

2. **Large Data Tests**: Need to test with realistic data volumes.

3. **Failure Scenarios**: Test transaction recovery, partial failures, concurrent access.

4. **Performance Benchmarks**: Measure transaction overhead, clone performance, query compilation time.

## Information for Other Agents

### For AI-DB
- Git-layer requires explicit `write_escalation_required()` call before writes
- Use `operation_complete(message)` after each operation for proper commits
- Transaction path available via `transaction.path` property

### For AI-Frontend
- No commit message callback available - must use explicit `operation_complete()`
- Working directory is `transaction.path` not `working_directory`
- All operations are synchronous

### For Console
- Git-layer has `recover(repo_path)` function for corrupted repos
- Transactions auto-rollback on exceptions
- Consider wrapping in `asyncio.to_thread()`

### For MCP
- Transaction model incompatible - needs complete redesign
- Consider maintaining transaction pool with context managers
- Repository path must be configured separately

## Summary

The main blocker is the fundamental interface mismatch between what git-layer provides and what every other component expects. This requires either significant adapter code or changes to align interfaces. The async/sync mismatch is solvable with wrappers, but the transaction lifecycle model difference (context manager vs stateful) requires architectural decisions.