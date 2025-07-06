"""Custom exceptions for ai-frontend."""


class AiFrontendError(Exception):
    """Base exception for ai-frontend."""

    pass


class ClaudeCodeError(AiFrontendError):
    """Exception raised when Claude Code CLI operations fail."""

    pass


class CompilationError(AiFrontendError):
    """Exception raised when frontend compilation fails."""

    pass


class GenerationError(AiFrontendError):
    """Exception raised when frontend generation fails."""

    pass


class ConfigurationError(AiFrontendError):
    """Exception raised for configuration issues."""

    pass


class TransactionError(AiFrontendError):
    """Exception raised for transaction-related issues."""

    pass
