from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TransactionProtocol(Protocol):
    """Interface that git-layer implements for transaction management.

    This protocol defines the contract between ai-db/ai-frontend and git-layer.
    Libraries call these methods to notify git-layer about operation outcomes.
    """

    @property
    def id(self) -> str:
        """Get the transaction ID."""
        ...

    @property
    def path(self) -> Path:
        """Get the current working directory path."""
        ...

    async def write_escalation_required(self) -> None:
        """Escalate to write mode by creating a temporary clone."""
        ...

    async def operation_complete(self, message: str) -> None:
        """Notify that an operation succeeded - git-layer should commit."""
        ...

    async def operation_failed(self, error_message: str) -> None:
        """Notify that an operation failed - git-layer should create failure branch."""
        ...
