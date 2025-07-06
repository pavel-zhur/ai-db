# Git-Layer

Git-Layer is a Python library that provides database-style transactions using Git as the underlying engine. It implements BEGIN, COMMIT, and ROLLBACK operations for file-based systems with full async support.

## Features

- **Async-first API** using Python async context managers
- **TransactionProtocol compliance** for integration with ai-db and ai-frontend
- **Write escalation** - read-only by default, write operations trigger temporary clones
- **Operation tracking** - libraries notify git-layer of success/failure for proper commit handling
- **Failure preservation** - failed operations create debugging branches
- **Crash recovery** - automatic cleanup of stale locks and incomplete transactions
- **Write locking** - prevents concurrent write transactions per repository

## Installation

This library is part of the AI-DB monorepo. Install using Poetry:

```bash
cd git-layer
poetry install
```

## Basic Usage

```python
import git_layer

# Begin a transaction
async with await git_layer.begin("/path/to/repo", message="Update data") as txn:
    # Signal that write operations will occur
    await txn.write_escalation_required()
    
    # Perform file operations using standard Python I/O
    with open(txn.path / "data.yaml", "w") as f:
        f.write("key: value\n")
    
    # Notify git-layer that operation succeeded
    await txn.operation_complete("Added data.yaml")
    
    # Transaction automatically commits on success
    # Or rolls back on exception
```

## Integration with AI Libraries

Git-layer implements the `TransactionProtocol` from ai-shared, allowing ai-db and ai-frontend to use it without tight coupling:

```python
from ai_shared.protocols import TransactionProtocol

# ai-db or ai-frontend receives this interface
async def process_with_transaction(txn: TransactionProtocol):
    # Access working directory
    data_file = txn.path / "data.yaml"
    
    # Signal write operations needed
    await txn.write_escalation_required()
    
    # Perform operations...
    
    # Notify success or failure
    await txn.operation_complete("Processed data")
    # or: await txn.operation_failed("Processing failed: reason")
```

## Transaction Lifecycle

### 1. Begin Transaction
```python
txn = await git_layer.begin("/path/to/repo", "Optional message")
async with txn:
    # Transaction operations
```

### 2. Write Escalation (Lazy)
```python
# Initially read-only, points to main branch
assert txn.path == Path("/path/to/repo")

# Write escalation creates temporary clone
await txn.write_escalation_required()
assert "git-layer-" in str(txn.path)  # Now points to temp clone
```

### 3. Operation Tracking
```python
# After successful operations
await txn.operation_complete("Description of what succeeded")

# After failed operations  
await txn.operation_failed("Description of what failed")
```

### 4. Commit/Rollback
```python
# Automatic on context manager exit
# Success -> commit (merge to main)
# Exception -> rollback (create rollback branch)
```

## Recovery

If a repository gets into a bad state (crashed processes, stale locks):

```python
# Recover repository to clean state
await git_layer.recover("/path/to/repo")
```

Recovery performs:
- Removes stale Git locks
- Removes write locks
- Resets to main branch with clean working tree
- Cleans up old transaction branches (24h+)
- Clears transaction tracking state

## Configuration

Configure using environment variables or Pydantic settings:

```python
from git_layer.config import GitLayerConfig

config = GitLayerConfig(
    git_user_name="My App",
    git_user_email="app@example.com",
    cleanup_old_branches_hours=48
)
```

Environment variables (with `GIT_LAYER_` prefix):
```bash
export GIT_LAYER_GIT_USER_NAME="My App"
export GIT_LAYER_GIT_USER_EMAIL="app@example.com"
export GIT_LAYER_CLEANUP_OLD_BRANCHES_HOURS=48
```

## Branch Naming Conventions

- **Transaction branches**: `transaction-{id}-{timestamp}`
- **Failure branches**: `failed-transaction-{timestamp}-{id}`
- **Rollback branches**: `transaction-{id}-{timestamp}` (preserved for debugging)

## Error Handling

Git-layer follows fail-fast principles with proper exception chaining:

```python
try:
    async with await git_layer.begin("/path/to/repo") as txn:
        # Operations that might fail
        pass
except git_layer.TransactionError as e:
    # Handle transaction-specific errors
    print(f"Transaction failed: {e}")
    # Original Git error available as e.__cause__
except git_layer.RepositoryError as e:
    # Handle repository-specific errors
    print(f"Repository error: {e}")
```

## Architecture

### Key Design Decisions

- **Async throughout**: All operations use `asyncio.to_thread()` for Git commands
- **Protocol-based**: Implements `TransactionProtocol` for loose coupling with consumers
- **Main branch protection**: Main always stays clean and committed
- **Write isolation**: Write operations happen in temporary clones
- **Debugging preservation**: Failed transactions create permanent branches
- **Simple locking**: File-based write locks prevent concurrent writes

### Transaction States

1. **Inactive**: Transaction not started
2. **Read-only**: Points to main branch, no writes allowed
3. **Write-escalated**: Temporary clone created, writes tracked
4. **Committed**: Changes merged to main, cleanup complete
5. **Rolled back**: Rollback branch created, main reset

## Testing

Run the test suite:

```bash
# All tests (all are async)
poetry run pytest

# Specific test categories
poetry run pytest tests/test_transaction_async.py  # Transaction functionality
poetry run pytest tests/test_repository_async.py   # Git repository operations
poetry run pytest tests/test_integration_async.py  # Integration scenarios

# With coverage
poetry run pytest --cov=git_layer
```

## Development

```bash
# Install dependencies
poetry install

# Run linting
poetry run mypy .
poetry run ruff check .
poetry run black --check .

# Format code
poetry run black .
poetry run ruff check --fix .
```

## Requirements

- **Python 3.13+**
- **Git** (command-line tool)
- **GitPython** library
- **Pydantic Settings** for configuration
- **ai-shared** for TransactionProtocol interface

## Limitations

- **No concurrent writes**: Only one write transaction per repository
- **Local repositories only**: No built-in remote Git server support
- **Branch accumulation**: Failed/rollback branches preserved indefinitely (by design)
- **Single-threaded design**: No internal concurrency control beyond write locks

## Integration Examples

### With ai-db
```python
import git_layer
from ai_db import AIDB

async with await git_layer.begin("/path/to/repo", "DB operation") as txn:
    db = AIDB(txn)  # ai-db receives TransactionProtocol
    result = await db.execute("SELECT * FROM users", permission="select")
```

### With ai-frontend
```python
import git_layer
from ai_frontend import AiFrontend

async with await git_layer.begin("/path/to/repo", "Frontend update") as txn:
    frontend = AiFrontend(txn)  # ai-frontend receives TransactionProtocol
    await frontend.generate_component("UserList", schema=user_schema)
```

## License

MIT License - see LICENSE file for details.