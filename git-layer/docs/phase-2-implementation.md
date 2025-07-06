# Phase 2 Implementation Details - git-layer

This document provides implementation details and architectural decisions for future maintainer agents working on the git-layer component.

## Architecture Overview

git-layer is a transaction management library that provides database-style BEGIN/COMMIT/ROLLBACK semantics using Git as the underlying engine. It serves as the foundation for ai-db and ai-frontend libraries.

### Core Design Principles

1. **Async-First**: All operations are async using `asyncio.to_thread()` for Git operations
2. **Protocol-Based**: Implements `TransactionProtocol` from ai-shared for loose coupling
3. **Fail-Safe**: Crashes leave harmless temporary files, main branch always clean
4. **Zero Dependencies**: Other libraries depend on git-layer, not vice versa

## Component Structure

```
src/git_layer/
├── __init__.py          # Public API (begin, recover functions)
├── transaction.py       # Transaction class implementing TransactionProtocol
├── repository.py        # GitRepository wrapper for Git operations
├── exceptions.py        # Custom exception hierarchy
├── config.py           # Pydantic configuration
└── utils.py            # Utility functions
```

## Key Implementation Details

### Transaction Flow

1. **Read-Only Default**: Transactions start read-only, pointing to main branch
2. **Write Escalation**: `write_escalation_required()` creates temporary clone in new branch
3. **Operation Tracking**: ai-db/ai-frontend call `operation_complete()` or `operation_failed()`
4. **Commit Process**: Merges transaction branch to main, cleans up temp folders
5. **Rollback Process**: Creates rollback branch for debugging, resets to main

### Branch Naming Convention

- **Transaction branches**: `transaction-{id}-{timestamp}`
- **Failure branches**: `failed-transaction-{timestamp}-{id}`
- **Rollback branches**: `transaction-{id}-{timestamp}` (kept for debugging)

### File Lock Strategy

Simple file-based write lock at `.git/ai-db-write.lock`:
- Created during write escalation
- Contains transaction ID
- Prevents concurrent write transactions
- Automatically cleaned up during recovery

### Error Handling Strategy

Following CLAUDE.md guidelines:
- **Transform exceptions**: Wrap Git errors in domain-specific exceptions
- **Preserve context**: Use exception chaining with `raise ... from e`
- **Fail fast**: No silent failures or defensive programming
- **Trust types**: Let type system prevent impossible states

### Recovery Mechanism

The `recover()` function handles crash recovery:
1. Removes stale locks (Git index lock, write lock)
2. Resets to main branch with clean working tree
3. Cleans up old transaction branches (24h+ old)
4. Clears transaction tracking state

### Testing Strategy

- **Behavior-focused**: Tests verify transaction semantics, not Git internals
- **Mock-friendly**: Can test with plain folders instead of Git repos
- **Async throughout**: All tests use pytest-asyncio
- **Recovery testing**: Simulates crashes and verifies cleanup

## Critical Implementation Notes

### Git Operations Thread Safety

All Git operations run in thread pool via `asyncio.to_thread()`:
```python
await asyncio.to_thread(self.repo.git.merge, branch_name, m=message)
```

### Remote Handling for Clones

When pushing from temporary clones back to original:
```python
# Must store Remote objects, not strings
remote = await asyncio.to_thread(
    self._original_repo.repo.create_remote, 
    remote_name, 
    str(self._working_repo.path)
)
```

### Master vs Main Branch Handling

GitPython creates "master" by default, code handles conversion:
```python
if "master" in [h.name for h in self.repo.heads]:
    self.repo.heads.master.rename("main")
```

### Transaction State Tracking

Class-level dictionary prevents nested transactions:
```python
_active_transactions: dict[str, str] = {}  # {repo_path: transaction_id}
```

## Configuration

Pydantic-based configuration with environment variable support:
```python
class GitLayerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GIT_LAYER_")
    git_user_name: str = "AI-DB System"
    git_user_email: str = "ai-db@localhost"
    # ... other settings
```

## Logging Strategy

- **INFO**: Normal operations (branch creation, commits, merges)
- **WARNING**: Expected but notable (stale locks, branch cleanup failures)
- **ERROR**: Unexpected failures (logged by exception handlers in calling code)

## Performance Considerations

- **Lazy cloning**: Only clone when write escalation needed
- **Minimal Git operations**: Use native Git commands for heavy operations
- **Efficient cleanup**: Remove old branches periodically, not per transaction

## Future Maintenance Notes

### Adding New Transaction Methods

1. Add method to `TransactionProtocol` in ai-shared
2. Implement in `Transaction` class
3. Add corresponding tests in `test_transaction_async.py`
4. Update integration tests if behavior changes

### Extending Configuration

1. Add fields to `GitLayerConfig`
2. Use environment variables with `GIT_LAYER_` prefix
3. Provide sensible defaults for backward compatibility

### Git Version Compatibility

Current implementation assumes Git 2.x+. Key dependencies:
- `git.merge` command for proper merge commits
- Branch creation/deletion APIs
- Remote operations for clone synchronization

### Error Message Guidelines

Follow this pattern for user-facing errors:
```python
raise TransactionError(f"Failed to {operation}: {underlying_error}") from e
```

This provides context while preserving the original error for debugging.

## Known Limitations

1. **No concurrent writes**: Only one write transaction per repository
2. **Local Git only**: No built-in support for remote Git servers
3. **Branch pollution**: Failed transactions create permanent branches (by design)
4. **No distributed transactions**: Each repository is isolated

## Testing Maintenance

### Test Categories

All tests are async and use pytest-asyncio 1.0+:

- **Repository tests**: Git operations and repository management (`test_repository_async.py`)
- **Transaction tests**: Transaction lifecycle and protocol compliance (`test_transaction_async.py`) 
- **Integration tests**: End-to-end workflows and recovery scenarios (`test_integration_async.py`)

### Test Data Management

- Uses temporary directories for complete isolation
- No shared state between tests
- Mock AI operations, use real Git repositories
- Automatic cleanup via pytest fixtures

### Test Coverage

- **31 async tests** covering all functionality
- **TransactionProtocol compliance** verified
- **Error scenarios** and crash recovery tested
- **Write locking** and concurrency constraints verified

### Adding New Tests

Follow existing async patterns:
```python
@pytest.mark.asyncio
async def test_new_behavior(temp_repo_path: Path):
    async with await git_layer.begin(str(temp_repo_path), "Test") as txn:
        # Test behavior, not implementation
        pass
```

Note: Only async tests exist. Synchronous API has been completely removed.