"""Git-Layer: Git-based transaction support for file operations.

This library provides database-style transactions using Git as the underlying engine.
It implements BEGIN, COMMIT, and ROLLBACK operations for file-based systems.

Example:
    >>> import git_layer
    >>> with git_layer.begin("/path/to/repo", message="Update data") as transaction:
    ...     # Signal write operations will occur
    ...     transaction.write_escalation_required()
    ...     # Perform file operations
    ...     with open(f"{transaction.path}/data.yaml", "w") as f:
    ...         f.write("key: value\\n")
    ...     # Transaction automatically commits on success
"""

import logging
from typing import Optional

from .transaction import Transaction
from .repository import GitRepository
from .exceptions import (
    GitLayerError,
    RepositoryError,
    TransactionError,
    TransactionStateError,
    GitOperationError,
)

__version__ = "0.1.0"
__all__ = [
    "begin",
    "recover",
    "Transaction",
    "GitRepository",
    "GitLayerError",
    "RepositoryError", 
    "TransactionError",
    "TransactionStateError",
    "GitOperationError",
]

# Configure logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


def begin(repo_path: str, message: Optional[str] = None) -> Transaction:
    """Begin a new transaction.
    
    Creates a new transaction context that can be used with Python's
    context manager (with statement). The transaction will automatically
    commit on success or rollback on failure.
    
    Args:
        repo_path: Path to the Git repository. Will be created if it doesn't exist.
        message: Optional message describing the transaction. Used in commit messages.
        
    Returns:
        A Transaction object that can be used as a context manager.
        
    Example:
        >>> with begin("/path/to/repo", message="Update schema") as txn:
        ...     # Write operations trigger automatic cloning
        ...     txn.write_escalation_required()
        ...     with open(f"{txn.path}/schema.yaml", "w") as f:
        ...         f.write("tables:\\n  users:\\n    - id\\n    - name\\n")
        ...     # Optionally commit after each operation
        ...     txn.operation_complete("Added schema.yaml")
        
    Raises:
        RepositoryError: If the repository cannot be initialized
        TransactionError: If the transaction cannot be started
    """
    transaction = Transaction(repo_path, message)
    return transaction


def recover(repo_path: str) -> None:
    """Recover a repository to a clean state.
    
    This function can be used to recover from crashes or other issues
    that leave the repository in an inconsistent state. It will:
    - Remove any Git locks
    - Reset to the main branch
    - Clean the working directory
    - Remove old transaction branches
    
    Args:
        repo_path: Path to the Git repository
        
    Raises:
        RepositoryError: If the repository cannot be recovered
    """
    repo = GitRepository(repo_path)
    repo.recover_to_clean_state()