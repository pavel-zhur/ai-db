# Git-Layer

Git-Layer is a Python library that provides database-style transactions using Git as the underlying engine. It implements BEGIN, COMMIT, and ROLLBACK operations for file-based systems.

## Features

- Simple transaction API using Python context managers
- Automatic Git repository initialization
- Write operations trigger temporary clones for isolation
- Every operation within a transaction creates a commit
- Main branch always stays in a clean, committed state
- Failed transactions are preserved in branches (not merged to main)

## Installation

```bash
pip install git-layer
```

## Usage

```python
import git_layer

# Begin a transaction
with git_layer.begin("/path/to/repo", message="Update data") as transaction:
    # Signal that write operations will occur
    transaction.write_escalation_required()
    
    # Perform file operations using standard Python I/O
    with open(f"{transaction.path}/data.yaml", "w") as f:
        f.write("key: value\n")
    
    # Optionally commit after each operation (for ai-db integration)
    transaction.operation_complete("Added data.yaml")
    
    # Transaction automatically commits on success
    # Or rolls back on exception
```

### Recovery

If a repository gets into a bad state, you can recover it:

```python
import git_layer

# Recover repository to clean state
git_layer.recover("/path/to/repo")
```

## How It Works

1. **BEGIN**: Creates a new branch for the transaction
2. **Write Escalation**: `write_escalation_required()` triggers creation of a temporary clone
3. **Operations**: Each file operation can be committed with `operation_complete()`
4. **COMMIT**: Merges the transaction branch to main
5. **ROLLBACK**: Commits current state to branch but doesn't merge to main

## Key Design Decisions

- **Main branch protection**: Main always stays in a clean, committed state
- **Write isolation**: Write operations happen in temporary clones
- **Failed transaction preservation**: Even failed transactions commit their state for debugging
- **No nested transactions**: Transactions cannot be nested
- **Single-threaded**: Designed for single-threaded operation

## Requirements

- Python 3.8+
- Git (command-line tool)
- GitPython library

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black git_layer tests

# Type check
mypy git_layer
```

## License

MIT License