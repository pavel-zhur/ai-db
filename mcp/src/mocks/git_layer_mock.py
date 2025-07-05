"""Mock implementation of Git-Layer for testing."""

from typing import Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
from ..protocols import GitLayerProtocol, TransactionContext


@dataclass
class MockTransaction:
    """Mock transaction context."""
    
    transaction_id: str
    working_directory: str = "/tmp/mock-transaction"
    
    async def write_escalation(self) -> str:
        """Mock write escalation."""
        return self.working_directory


class MockGitLayer:
    """Mock Git-Layer implementation for testing."""
    
    def __init__(self, repo_path: str) -> None:
        """Initialize mock Git-Layer."""
        self._repo_path = repo_path
        self._transaction_counter = 0
    
    @asynccontextmanager
    async def transaction(self, commit_message: Optional[str] = None):
        """Create a mock transaction context."""
        self._transaction_counter += 1
        transaction_id = f"mock-transaction-{self._transaction_counter}"
        
        transaction = MockTransaction(
            transaction_id=transaction_id,
            working_directory=f"/tmp/{transaction_id}",
        )
        
        try:
            yield transaction
            # Mock commit on successful exit
            if commit_message:
                print(f"Mock commit: {commit_message}")
        except Exception:
            # Mock rollback on error
            print(f"Mock rollback: {transaction_id}")
            raise
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        self._transaction_counter += 1
        return f"mock-transaction-{self._transaction_counter}"
    
    async def commit_transaction(self, transaction_id: str, commit_message: str) -> None:
        """Commit a transaction."""
        print(f"Mock commit transaction {transaction_id}: {commit_message}")
    
    async def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a transaction."""
        print(f"Mock rollback transaction {transaction_id}")