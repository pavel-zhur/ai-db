"""Tests for Transaction class."""

import pytest
from pathlib import Path

import git_layer
from git_layer.transaction import Transaction
from git_layer.exceptions import TransactionError, TransactionStateError


def test_transaction_basic(temp_repo_path: Path):
    """Test basic transaction flow."""
    with git_layer.begin(str(temp_repo_path), message="Test transaction") as txn:
        assert txn.is_active
        assert txn.transaction_id
        assert txn.path == str(temp_repo_path)
    
    # Transaction should be inactive after context exit
    assert not txn.is_active


def test_transaction_write_operations(temp_repo_path: Path, test_file_content: str):
    """Test transaction with write operations."""
    test_file = "data.yaml"
    
    with git_layer.begin(str(temp_repo_path), message="Add data") as txn:
        # Signal write escalation
        txn.write_escalation_required()
        
        # Path should now be a clone
        assert txn.path != str(temp_repo_path)
        assert "git-layer-" in txn.path
        
        # Write file
        file_path = Path(txn.path) / test_file
        file_path.write_text(test_file_content)
        
        # File should exist in transaction
        assert file_path.exists()
    
    # After commit, file should exist in original repo
    assert (temp_repo_path / test_file).exists()
    assert (temp_repo_path / test_file).read_text() == test_file_content


def test_transaction_rollback(temp_repo_path: Path):
    """Test transaction rollback on exception."""
    test_file = "rollback.txt"
    
    with pytest.raises(ValueError):
        with git_layer.begin(str(temp_repo_path), message="Failing transaction") as txn:
            txn.write_escalation_required()
            
            # Write file
            file_path = Path(txn.path) / test_file
            file_path.write_text("This should be rolled back")
            
            # Raise exception
            raise ValueError("Simulated error")
    
    # File should not exist in original repo
    assert not (temp_repo_path / test_file).exists()


def test_transaction_checkpoint(temp_repo_path: Path):
    """Test creating checkpoints during transaction."""
    with git_layer.begin(str(temp_repo_path), message="Checkpoint test") as txn:
        txn.write_escalation_required()
        
        # First checkpoint
        (Path(txn.path) / "file1.txt").write_text("content1")
        txn.checkpoint("Add file1")
        
        # Second checkpoint
        (Path(txn.path) / "file2.txt").write_text("content2")
        txn.checkpoint("Add file2")
    
    # Both files should exist
    assert (temp_repo_path / "file1.txt").exists()
    assert (temp_repo_path / "file2.txt").exists()


def test_transaction_operation_complete(temp_repo_path: Path):
    """Test operation_complete method for ai-db integration."""
    with git_layer.begin(str(temp_repo_path), message="Operations test") as txn:
        txn.write_escalation_required()
        
        # First operation
        (Path(txn.path) / "table1.yaml").write_text("id: 1\nname: test")
        txn.operation_complete("Created table1")
        
        # Second operation
        (Path(txn.path) / "table2.yaml").write_text("id: 2\nname: test2")
        txn.operation_complete("Created table2")
    
    # Both files should exist
    assert (temp_repo_path / "table1.yaml").exists()
    assert (temp_repo_path / "table2.yaml").exists()


def test_transaction_no_writes(temp_repo_path: Path):
    """Test transaction with no write operations."""
    with git_layer.begin(str(temp_repo_path), message="Read-only transaction") as txn:
        # Don't call write_escalation_required
        assert txn.path == str(temp_repo_path)
    
    # Should complete successfully without creating branches


def test_transaction_nested_error(temp_repo_path: Path):
    """Test that nested transactions are not allowed."""
    with git_layer.begin(str(temp_repo_path), message="Outer") as txn1:
        txn2 = Transaction(str(temp_repo_path), message="Inner")
        
        with pytest.raises(TransactionStateError, match="already active"):
            txn2.begin()


def test_transaction_double_commit(temp_repo_path: Path):
    """Test that double commit raises error."""
    txn = Transaction(str(temp_repo_path), message="Test")
    txn.begin()
    txn.commit()
    
    with pytest.raises(TransactionStateError, match="already committed"):
        txn.commit()


def test_transaction_operations_without_begin(temp_repo_path: Path):
    """Test that operations without begin raise errors."""
    txn = Transaction(str(temp_repo_path), message="Test")
    
    with pytest.raises(TransactionStateError, match="No active transaction"):
        txn.write_escalation_required()
    
    with pytest.raises(TransactionStateError, match="No active transaction"):
        txn.checkpoint()
    
    with pytest.raises(TransactionStateError, match="No active transaction"):
        txn.commit()


def test_transaction_multiple_files(temp_repo_path: Path):
    """Test transaction with multiple file operations."""
    files = {
        "config.yaml": "setting: value",
        "data/users.yaml": "- name: Alice\n- name: Bob",
        "data/products.yaml": "- id: 1\n  name: Product A",
    }
    
    with git_layer.begin(str(temp_repo_path), message="Add multiple files") as txn:
        txn.write_escalation_required()
        
        for file_path, content in files.items():
            full_path = Path(txn.path) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
    
    # All files should exist
    for file_path, content in files.items():
        assert (temp_repo_path / file_path).exists()
        assert (temp_repo_path / file_path).read_text() == content


def test_transaction_modify_existing(temp_repo_path: Path):
    """Test modifying existing files in a transaction."""
    # Create initial file
    existing_file = temp_repo_path / "existing.txt"
    existing_file.write_text("original content")
    
    # Commit it
    from git_layer.repository import GitRepository
    repo = GitRepository(str(temp_repo_path))
    repo.commit_all("Add existing file")
    
    # Modify in transaction
    with git_layer.begin(str(temp_repo_path), message="Modify existing") as txn:
        txn.write_escalation_required()
        
        file_path = Path(txn.path) / "existing.txt"
        file_path.write_text("modified content")
    
    # Should have new content
    assert existing_file.read_text() == "modified content"


def test_transaction_recovery_after_crash(temp_repo_path: Path):
    """Test recovery after simulated crash."""
    # Start a transaction and simulate crash
    txn = Transaction(str(temp_repo_path), message="Crashed transaction")
    txn.begin()
    txn.write_escalation_required()
    
    # Write some data
    (Path(txn.path) / "crash.txt").write_text("crashed data")
    
    # Simulate crash - don't call commit or rollback
    del txn
    
    # Create new transaction - should work
    with git_layer.begin(str(temp_repo_path), message="After crash") as txn2:
        txn2.write_escalation_required()
        (Path(txn2.path) / "recovered.txt").write_text("recovered")
    
    # Only recovered file should exist
    assert not (temp_repo_path / "crash.txt").exists()
    assert (temp_repo_path / "recovered.txt").exists()