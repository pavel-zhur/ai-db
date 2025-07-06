"""Tests for ai-shared protocols."""

from pathlib import Path

from ai_shared import TransactionProtocol


def test_transaction_protocol_interface() -> None:
    """Test that TransactionProtocol interface is properly defined."""

    class MockTransaction:
        """Mock implementation of TransactionProtocol for testing."""

        @property
        def id(self) -> str:
            return "test-id"

        @property
        def path(self) -> Path:
            return Path("/test/path")

        async def write_escalation_required(self) -> None:
            pass

        async def operation_complete(self, message: str) -> None:
            pass

        async def operation_failed(self, error_message: str) -> None:
            pass

    # Verify the mock satisfies the protocol
    mock = MockTransaction()
    assert isinstance(mock.id, str)
    assert isinstance(mock.path, Path)

    # Type checking will verify this implements TransactionProtocol
    def uses_transaction(transaction: TransactionProtocol) -> str:
        return transaction.id

    result = uses_transaction(mock)
    assert result == "test-id"
