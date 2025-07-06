"""Custom exceptions for AI-DB."""



class AIDBError(Exception):
    """Base exception for AI-DB."""

    pass


class PermissionError(AIDBError):
    """Raised when operation exceeds granted permissions."""

    def __init__(self, required: str, granted: str) -> None:
        super().__init__(
            f"Operation requires {required} permission, but only {granted} was granted"
        )
        self.required = required
        self.granted = granted


class SchemaError(AIDBError):
    """Raised for schema-related errors."""

    pass


class ValidationError(AIDBError):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: list[str] | None = None) -> None:
        super().__init__(message)
        self.details = details or []


class ConstraintViolationError(ValidationError):
    """Raised when a constraint is violated."""

    def __init__(self, constraint_name: str, message: str, table: str | None = None) -> None:
        super().__init__(message)
        self.constraint_name = constraint_name
        self.table = table


class CompilationError(AIDBError):
    """Raised when query compilation fails."""

    pass


class AIError(AIDBError):
    """Raised when AI operations fail."""

    def __init__(self, message: str, retry_count: int = 0) -> None:
        super().__init__(message)
        self.retry_count = retry_count


class StorageError(AIDBError):
    """Raised for storage-related errors."""

    pass


class TransactionError(AIDBError):
    """Raised for transaction-related errors."""

    pass
