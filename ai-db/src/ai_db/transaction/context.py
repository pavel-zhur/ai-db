"""Transaction context management for AI-DB."""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from ai_db.core.models import TransactionContext
from ai_db.exceptions import TransactionError

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manages transaction context for AI-DB operations."""
    
    def __init__(self, transaction_context: TransactionContext) -> None:
        self._context = transaction_context
        self._original_working_dir = transaction_context.working_directory
        self._is_escalated = False
    
    @property
    def transaction_id(self) -> str:
        """Get the current transaction ID."""
        return self._context.transaction_id
    
    @property
    def working_directory(self) -> str:
        """Get the current working directory."""
        return self._context.working_directory
    
    @property
    def is_write_escalated(self) -> bool:
        """Check if transaction is escalated for writes."""
        return self._context.is_write_escalated
    
    def escalate_write(self) -> str:
        """Escalate transaction for write operations."""
        if self._context.is_write_escalated:
            return self._context.working_directory
        
        try:
            # Call the git-layer escalation method
            new_directory = self._context.escalate_write()
            self._context.working_directory = new_directory
            self._context.is_write_escalated = True
            self._is_escalated = True
            
            logger.info(f"Transaction {self.transaction_id} escalated for writes to {new_directory}")
            return new_directory
            
        except Exception as e:
            raise TransactionError(f"Failed to escalate transaction: {str(e)}")
    
    def get_metadata(self) -> Dict[str, Any]:
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


class MockTransactionContext(TransactionContext):
    """Mock transaction context for testing."""
    
    def __init__(self, transaction_id: str = "test-txn", working_directory: str = "/tmp/ai-db-test"):
        super().__init__(transaction_id, working_directory)
        self._escalate_count = 0
    
    def escalate_write(self) -> str:
        """Mock escalation."""
        self._escalate_count += 1
        new_dir = f"{self.working_directory}-write-{self._escalate_count}"
        self.working_directory = new_dir
        self.is_write_escalated = True
        return new_dir