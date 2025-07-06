"""Mock implementation of Git-Layer for testing."""

from pathlib import Path

from ai_shared.protocols import TransactionProtocol


class MockTransaction:
    """Mock transaction context implementing TransactionProtocol."""

    def __init__(self, transaction_id: str, repo_path: Path):
        self._id = transaction_id
        self._path = repo_path / "mock_workspace"
        self._path.mkdir(parents=True, exist_ok=True)

    @property
    def id(self) -> str:
        """Get the transaction ID."""
        return self._id

    @property
    def path(self) -> Path:
        """Get the current working directory path."""
        return self._path

    async def write_escalation_required(self) -> None:
        """Escalate to write mode by creating a temporary clone."""
        print(f"Mock: Write escalation for transaction {self._id}")

    async def operation_complete(self, message: str) -> None:
        """Notify that an operation succeeded - git-layer should commit."""
        print(f"Mock: Operation complete - {message} (transaction {self._id})")

    async def operation_failed(self, error_message: str) -> None:
        """Notify that an operation failed - git-layer should create failure branch."""
        print(f"Mock: Operation failed - {error_message} (transaction {self._id})")


class MockGitLayer:
    """Mock Git-Layer implementation for testing."""

    def __init__(self, repo_path: Path):
        """Initialize mock Git-Layer."""
        self._repo_path = Path(repo_path)
        self._transaction_counter = 0

    async def begin(self, repo_path: Path, message: str) -> TransactionProtocol:
        """Begin a new transaction."""
        self._transaction_counter += 1
        transaction_id = f"mock-transaction-{self._transaction_counter}"
        print(f"Mock: Begin transaction {transaction_id} - {message}")
        return MockTransaction(transaction_id, repo_path)

    async def recover(self, repo_path: Path) -> None:
        """Recover repository to clean state."""
        print(f"Mock: Recover repository at {repo_path}")
