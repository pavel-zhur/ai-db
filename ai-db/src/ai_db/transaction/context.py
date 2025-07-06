"""Transaction context management for AI-DB."""

import logging
from contextlib import contextmanager
from typing import Any

from ai_shared.protocols import TransactionProtocol

from ai_db.exceptions import TransactionError

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manages transaction context for AI-DB operations."""

    def __init__(self, transaction_context: TransactionProtocol) -> None:
        self._context = transaction_context
        self._original_working_dir = str(transaction_context.path)
        self._is_escalated = False

    @property
    def transaction_id(self) -> str:
        """Get the current transaction ID."""
        return self._context.id

    @property
    def working_directory(self) -> str:
        """Get the current working directory."""
        return str(self._context.path)

    @property
    def is_write_escalated(self) -> bool:
        """Check if transaction is escalated for writes."""
        return self._is_escalated

    async def escalate_write(self) -> str:
        """Escalate transaction for write operations."""
        if self._is_escalated:
            return str(self._context.path)

        try:
            # Call the git-layer escalation method
            await self._context.write_escalation_required()
            self._is_escalated = True

            logger.info(f"Transaction {self.transaction_id} escalated for writes")
            return str(self._context.path)

        except Exception as e:
            raise TransactionError(f"Failed to escalate transaction: {e!s}")

    def get_metadata(self) -> dict[str, Any]:
        """Get transaction metadata."""
        return {
            "transaction_id": self.transaction_id,
            "working_directory": self.working_directory,
            "is_write_escalated": self.is_write_escalated,
            "original_directory": self._original_working_dir,
        }

    @contextmanager
    def savepoint(self, name: str):
        """Create a savepoint within the transaction."""
        # For now, savepoints are not implemented
        # This is a placeholder for future functionality
        logger.debug(f"Savepoint {name} created (not implemented)")
        try:
            yield
        finally:
            logger.debug(f"Savepoint {name} released (not implemented)")
