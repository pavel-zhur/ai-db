"""Custom exceptions for git-layer."""

from typing import Optional


class GitLayerError(Exception):
    """Base exception for all git-layer errors."""
    pass


class RepositoryError(GitLayerError):
    """Raised when there are issues with the Git repository."""
    pass


class TransactionError(GitLayerError):
    """Raised when there are issues with transaction operations."""
    pass


class TransactionStateError(TransactionError):
    """Raised when transaction is in an invalid state for the requested operation."""
    pass


class GitOperationError(GitLayerError):
    """Raised when a Git operation fails."""
    
    def __init__(self, message: str, git_error: Optional[Exception] = None):
        super().__init__(message)
        self.git_error = git_error