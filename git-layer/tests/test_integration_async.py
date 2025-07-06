"""Async integration tests for git-layer."""

import asyncio
import pytest
from pathlib import Path

import git_layer
from git_layer.repository import GitRepository
from git_layer.exceptions import TransactionError, TransactionStateError


@pytest.mark.asyncio
async def test_concurrent_read_transactions(temp_repo_path: Path):
    """Test concurrent read-only transactions."""
    # Create initial data
    (temp_repo_path / "data.txt").write_text("initial data")
    repo = GitRepository(str(temp_repo_path))
    await repo.commit_all("Initial data")
    
    async def read_transaction(txn_id: int):
        """Perform a read transaction."""
        async with await git_layer.begin(str(temp_repo_path), f"Read {txn_id}") as txn:
            # Read without escalation
            content = (txn.path / "data.txt").read_text()
            assert content == "initial data"
            await asyncio.sleep(0.1)  # Simulate work
        return txn_id
    
    # Run multiple read transactions concurrently
    tasks = [read_transaction(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5


@pytest.mark.asyncio
async def test_sequential_write_transactions(temp_repo_path: Path):
    """Test sequential write transactions."""
    for i in range(3):
        async with await git_layer.begin(str(temp_repo_path), f"Write {i}") as txn:
            await txn.write_escalation_required()
            
            # Write a file
            (txn.path / f"file{i}.txt").write_text(f"content {i}")
            await txn.operation_complete(f"Added file{i}")
    
    # All files should exist
    for i in range(3):
        assert (temp_repo_path / f"file{i}.txt").exists()
        assert (temp_repo_path / f"file{i}.txt").read_text() == f"content {i}"


@pytest.mark.asyncio
async def test_complex_workflow(temp_repo_path: Path):
    """Test a complex workflow with multiple operations."""
    # Initial setup
    async with await git_layer.begin(str(temp_repo_path), "Initial setup") as txn:
        await txn.write_escalation_required()
        
        # Create directory structure
        (txn.path / "db").mkdir()
        (txn.path / "frontend").mkdir()
        
        # Add initial files
        (txn.path / "db" / "schema.yaml").write_text("tables: []")
        (txn.path / "frontend" / "config.json").write_text('{"theme": "light"}')
        
        await txn.operation_complete("Created initial structure")
    
    # Simulate AI-DB operation
    async with await git_layer.begin(str(temp_repo_path), "Create table") as txn:
        await txn.write_escalation_required()
        
        # Add table definition
        (txn.path / "db" / "users.yaml").write_text("""
table: users
columns:
  - name: id
    type: integer
  - name: name
    type: string
""")
        await txn.operation_complete("Created users table")
    
    # Simulate AI-Frontend operation
    async with await git_layer.begin(str(temp_repo_path), "Update theme") as txn:
        await txn.write_escalation_required()
        
        # Update config
        (txn.path / "frontend" / "config.json").write_text('{"theme": "dark"}')
        await txn.operation_complete("Updated theme to dark")
    
    # Verify final state
    assert (temp_repo_path / "db" / "schema.yaml").exists()
    assert (temp_repo_path / "db" / "users.yaml").exists()
    assert (temp_repo_path / "frontend" / "config.json").exists()
    assert '"theme": "dark"' in (temp_repo_path / "frontend" / "config.json").read_text()


@pytest.mark.asyncio
async def test_failure_recovery_workflow(temp_repo_path: Path):
    """Test failure and recovery workflow."""
    # Successful operation
    async with await git_layer.begin(str(temp_repo_path), "Success") as txn:
        await txn.write_escalation_required()
        (txn.path / "success.txt").write_text("success")
        await txn.operation_complete("Successful operation")
    
    # Failed operation
    try:
        async with await git_layer.begin(str(temp_repo_path), "Failure") as txn:
            await txn.write_escalation_required()
            
            # Create some data
            (txn.path / "partial.txt").write_text("partial data")
            
            # Report failure
            await txn.operation_failed("Database constraint violation")
            
            # Simulate deciding to rollback
            raise TransactionError("Cannot proceed after failure")
    except TransactionError:
        pass
    
    # Verify state
    assert (temp_repo_path / "success.txt").exists()
    assert not (temp_repo_path / "partial.txt").exists()
    
    # Check failure branch exists
    repo = GitRepository(str(temp_repo_path))
    branches = await repo.get_branches()
    failure_branches = [b for b in branches if b.startswith("failed-transaction-")]
    assert len(failure_branches) == 1


@pytest.mark.asyncio
async def test_transaction_implements_protocol(temp_repo_path: Path):
    """Test that transaction properly implements TransactionProtocol."""
    from ai_shared.protocols import TransactionProtocol
    
    txn = await git_layer.begin(str(temp_repo_path), "Protocol test")
    
    # Should implement protocol
    assert isinstance(txn, TransactionProtocol)
    
    # Test all protocol methods
    async with txn:
        # Test properties
        assert isinstance(txn.id, str)
        assert isinstance(txn.path, Path)
        
        # Test methods
        await txn.write_escalation_required()
        
        (txn.path / "test.txt").write_text("test")
        await txn.operation_complete("Test operation")
        
        # Test failure reporting (without actually failing)
        await txn.operation_failed("Test failure")


@pytest.mark.asyncio 
async def test_recovery_after_incomplete_transaction(temp_repo_path: Path):
    """Test recovery after incomplete transaction."""
    # Start transaction but don't complete it
    txn = git_layer.Transaction(str(temp_repo_path), "Incomplete")
    await txn.begin()
    await txn.write_escalation_required()
    
    # Write some data
    (txn.path / "incomplete.txt").write_text("incomplete")
    
    # Abandon transaction (simulate crash)
    txn_path = str(txn.path)
    del txn
    
    # Recover repository
    await git_layer.recover(str(temp_repo_path))
    
    # Should be able to start new transaction
    async with await git_layer.begin(str(temp_repo_path), "After recovery") as new_txn:
        await new_txn.write_escalation_required()
        (new_txn.path / "recovered.txt").write_text("recovered")
    
    # Verify state
    assert not (temp_repo_path / "incomplete.txt").exists()
    assert (temp_repo_path / "recovered.txt").exists()