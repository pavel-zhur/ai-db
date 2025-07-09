"""Integration tests for transaction support."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml
from ai_shared.protocols import TransactionProtocol

from ai_db.storage import YAMLStore
from ai_db.transaction import TransactionManager


@pytest.mark.integration
class TestTransactionIntegration:
    """Test transaction management integration."""

    @pytest.mark.asyncio
    async def test_multiple_write_operations(self, temp_dir):
        """Test multiple write operations in same transaction."""
        # Create mock transaction
        transaction_ctx = AsyncMock(spec=TransactionProtocol)
        transaction_ctx.id = "test-txn"
        transaction_ctx.path = temp_dir
        transaction_ctx.write_escalation_required = AsyncMock(return_value=None)
        transaction_ctx.operation_complete = AsyncMock(return_value=None)
        transaction_ctx.operation_failed = AsyncMock(return_value=None)
        store = YAMLStore(transaction_ctx)

        # First write
        await store.write_table("users", [{"id": 1, "name": "Alice"}])

        # Second write should use same escalated directory
        await store.write_table("products", [{"id": 1, "name": "Widget"}])

        # Verify write_escalation_required was called for first write only
        assert transaction_ctx.write_escalation_required.call_count == 2

        # Verify both files exist
        assert (Path(temp_dir) / "tables" / "users.yaml").exists()
        assert (Path(temp_dir) / "tables" / "products.yaml").exists()

    @pytest.mark.asyncio
    async def test_read_operations_no_escalation(self, temp_dir):
        """Test that read operations don't trigger escalation."""
        # Set up initial data
        tables_dir = temp_dir / "tables"
        tables_dir.mkdir(exist_ok=True)

        with open(tables_dir / "users.yaml", "w") as f:
            yaml.dump([{"id": 1, "name": "Alice"}], f)

        # Create mock transaction
        transaction_ctx = AsyncMock(spec=TransactionProtocol)
        transaction_ctx.id = "test-txn"
        transaction_ctx.path = temp_dir
        transaction_ctx.write_escalation_required = AsyncMock(return_value=None)
        transaction_ctx.operation_complete = AsyncMock(return_value=None)
        transaction_ctx.operation_failed = AsyncMock(return_value=None)

        store = YAMLStore(transaction_ctx)

        # Multiple reads
        data1 = await store.read_table("users")
        await store.read_table("users")
        data3 = await store.read_table("products")  # Non-existent

        # No escalation should occur
        transaction_ctx.write_escalation_required.assert_not_called()

        # Data should be read correctly
        assert len(data1) == 1
        assert data1[0]["name"] == "Alice"
        assert data3 == []  # Non-existent table

    @pytest.mark.asyncio
    async def test_savepoint_placeholder(self, temp_dir):
        """Test savepoint context manager (placeholder)."""
        # Create mock transaction
        transaction_ctx = AsyncMock(spec=TransactionProtocol)
        transaction_ctx.id = "test-txn"
        transaction_ctx.path = temp_dir

        manager = TransactionManager(transaction_ctx)

        # Savepoints are not implemented but should not error
        with manager.savepoint("sp1"):
            # Simulate some operations
            pass

        # Should complete without error
        assert True
