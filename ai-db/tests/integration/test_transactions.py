"""Integration tests for transaction support."""

import pytest
from pathlib import Path
import yaml

from ai_db.storage import YAMLStore
from ai_db.transaction import TransactionManager
from ai_db.transaction.context import MockTransactionContext


class TestTransactionIntegration:
    """Test transaction management integration."""
    
    @pytest.mark.asyncio
    async def test_transaction_write_escalation(self, temp_dir):
        """Test that writes trigger transaction escalation."""
        transaction_ctx = MockTransactionContext("test-txn", str(temp_dir))
        manager = TransactionManager(transaction_ctx)
        
        # Initially not escalated
        assert not manager.is_write_escalated
        original_dir = manager.working_directory
        
        # Create YAML store
        store = YAMLStore(transaction_ctx)
        
        # Write should trigger escalation
        await store.write_table("test", [{"id": 1}])
        
        # Check escalation happened
        assert manager.is_write_escalated
        assert manager.working_directory != original_dir
        assert "write" in manager.working_directory
    
    @pytest.mark.asyncio
    async def test_transaction_metadata(self, temp_dir):
        """Test transaction metadata tracking."""
        transaction_ctx = MockTransactionContext("test-txn-456", str(temp_dir))
        manager = TransactionManager(transaction_ctx)
        
        # Get initial metadata
        metadata = manager.get_metadata()
        assert metadata["transaction_id"] == "test-txn-456"
        assert metadata["is_write_escalated"] is False
        assert metadata["working_directory"] == str(temp_dir)
        assert metadata["original_directory"] == str(temp_dir)
        
        # Escalate
        manager.escalate_write()
        
        # Check updated metadata
        metadata = manager.get_metadata()
        assert metadata["is_write_escalated"] is True
        assert metadata["working_directory"] != metadata["original_directory"]
    
    @pytest.mark.asyncio
    async def test_multiple_write_operations(self, temp_dir):
        """Test multiple write operations in same transaction."""
        transaction_ctx = MockTransactionContext("test-txn", str(temp_dir))
        store = YAMLStore(transaction_ctx)
        
        # First write
        await store.write_table("users", [{"id": 1, "name": "Alice"}])
        first_dir = transaction_ctx.working_directory
        
        # Second write should use same escalated directory
        await store.write_table("products", [{"id": 1, "name": "Widget"}])
        second_dir = transaction_ctx.working_directory
        
        assert first_dir == second_dir
        assert transaction_ctx.is_write_escalated
        
        # Verify both files exist
        assert (Path(second_dir) / "tables" / "users.yaml").exists()
        assert (Path(second_dir) / "tables" / "products.yaml").exists()
    
    @pytest.mark.asyncio
    async def test_read_operations_no_escalation(self, temp_dir):
        """Test that read operations don't trigger escalation."""
        # Set up initial data
        tables_dir = temp_dir / "tables"
        tables_dir.mkdir(exist_ok=True)
        
        with open(tables_dir / "users.yaml", "w") as f:
            yaml.dump([{"id": 1, "name": "Alice"}], f)
        
        transaction_ctx = MockTransactionContext("test-txn", str(temp_dir))
        store = YAMLStore(transaction_ctx)
        
        # Multiple reads
        data1 = await store.read_table("users")
        data2 = await store.read_table("users")
        data3 = await store.read_table("products")  # Non-existent
        
        # No escalation should occur
        assert not transaction_ctx.is_write_escalated
        assert transaction_ctx.working_directory == str(temp_dir)
        
        # Data should be read correctly
        assert len(data1) == 1
        assert data1[0]["name"] == "Alice"
        assert data3 == []  # Non-existent table
    
    @pytest.mark.asyncio
    async def test_savepoint_placeholder(self, temp_dir):
        """Test savepoint context manager (placeholder)."""
        transaction_ctx = MockTransactionContext("test-txn", str(temp_dir))
        manager = TransactionManager(transaction_ctx)
        
        # Savepoints are not implemented but should not error
        with manager.savepoint("sp1"):
            # Simulate some operations
            pass
        
        # Should complete without error
        assert True