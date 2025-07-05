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
    # Perform file operations using standard Python I/O
    with open(f"{transaction.path}/data.yaml", "w") as f:
        f.write("key: value\n")
    
    # Transaction automatically commits on success
    # Or rolls back on exception
```

## How It Works

1. **BEGIN**: Creates a new branch for the transaction
2. **Write Operations**: Trigger creation of a temporary clone
3. **Operations**: Each file operation creates a commit
4. **COMMIT**: Merges the transaction branch to main
5. **ROLLBACK**: Abandons the branch without merging

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