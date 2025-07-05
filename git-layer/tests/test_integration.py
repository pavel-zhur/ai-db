"""Integration tests for git-layer."""

import pytest
from pathlib import Path
import concurrent.futures
import time

import git_layer
from git_layer.repository import GitRepository


def test_sequential_transactions(temp_repo_path: Path):
    """Test multiple sequential transactions."""
    # Transaction 1: Create initial data
    with git_layer.begin(str(temp_repo_path), message="Initial data") as txn:
        txn.write_escalation_required()
        (Path(txn.path) / "users.yaml").write_text("- id: 1\n  name: Alice")
    
    # Transaction 2: Add more data
    with git_layer.begin(str(temp_repo_path), message="Add Bob") as txn:
        txn.write_escalation_required()
        users_file = Path(txn.path) / "users.yaml"
        content = users_file.read_text()
        users_file.write_text(content + "\n- id: 2\n  name: Bob")
    
    # Transaction 3: Add different file
    with git_layer.begin(str(temp_repo_path), message="Add products") as txn:
        txn.write_escalation_required()
        (Path(txn.path) / "products.yaml").write_text("- id: 1\n  name: Widget")
    
    # Verify all changes
    assert (temp_repo_path / "users.yaml").exists()
    assert "Alice" in (temp_repo_path / "users.yaml").read_text()
    assert "Bob" in (temp_repo_path / "users.yaml").read_text()
    assert (temp_repo_path / "products.yaml").exists()


def test_failed_transaction_recovery(temp_repo_path: Path):
    """Test recovery from failed transactions."""
    # Successful transaction
    with git_layer.begin(str(temp_repo_path), message="Success") as txn:
        txn.write_escalation_required()
        (Path(txn.path) / "good.txt").write_text("good data")
    
    # Failed transaction
    try:
        with git_layer.begin(str(temp_repo_path), message="Failure") as txn:
            txn.write_escalation_required()
            (Path(txn.path) / "bad.txt").write_text("bad data")
            raise RuntimeError("Simulated failure")
    except RuntimeError:
        pass
    
    # Another successful transaction
    with git_layer.begin(str(temp_repo_path), message="After failure") as txn:
        txn.write_escalation_required()
        (Path(txn.path) / "recovery.txt").write_text("recovered")
    
    # Check state
    assert (temp_repo_path / "good.txt").exists()
    assert not (temp_repo_path / "bad.txt").exists()
    assert (temp_repo_path / "recovery.txt").exists()


def test_transaction_with_subdirectories(temp_repo_path: Path):
    """Test transactions with complex directory structures."""
    structure = {
        "config/app.yaml": "name: MyApp\nversion: 1.0",
        "data/2024/01/sales.yaml": "- amount: 100\n- amount: 200",
        "data/2024/02/sales.yaml": "- amount: 150\n- amount: 250",
        "schemas/tables.yaml": "users:\n  - id\n  - name",
    }
    
    with git_layer.begin(str(temp_repo_path), message="Complex structure") as txn:
        txn.write_escalation_required()
        
        for file_path, content in structure.items():
            full_path = Path(txn.path) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
    
    # Verify structure
    for file_path in structure:
        assert (temp_repo_path / file_path).exists()


def test_large_transaction(temp_repo_path: Path):
    """Test transaction with many files."""
    num_files = 100
    
    with git_layer.begin(str(temp_repo_path), message="Large transaction") as txn:
        txn.write_escalation_required()
        
        data_dir = Path(txn.path) / "data"
        data_dir.mkdir(exist_ok=True)
        
        for i in range(num_files):
            file_path = data_dir / f"file_{i:04d}.txt"
            file_path.write_text(f"Content for file {i}")
            
            # Create checkpoints every 25 files
            if i % 25 == 24:
                txn.checkpoint(f"Added files up to {i + 1}")
    
    # Verify all files
    data_dir = temp_repo_path / "data"
    assert len(list(data_dir.glob("*.txt"))) == num_files


def test_binary_files(temp_repo_path: Path):
    """Test handling binary files in transactions."""
    binary_data = b"\x00\x01\x02\x03\x04\x05"
    
    with git_layer.begin(str(temp_repo_path), message="Binary files") as txn:
        txn.write_escalation_required()
        
        # Write binary file
        binary_file = Path(txn.path) / "data.bin"
        binary_file.write_bytes(binary_data)
        
        # Write text file
        text_file = Path(txn.path) / "data.txt"
        text_file.write_text("text data")
    
    # Verify files
    assert (temp_repo_path / "data.bin").read_bytes() == binary_data
    assert (temp_repo_path / "data.txt").read_text() == "text data"


def test_empty_transaction(temp_repo_path: Path):
    """Test transaction with no operations."""
    # Transaction with no writes
    with git_layer.begin(str(temp_repo_path), message="Empty") as txn:
        pass  # Do nothing
    
    # Should complete successfully


def test_git_history(temp_repo_path: Path):
    """Test that transactions create proper Git history."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create some transactions
    messages = [
        "First transaction",
        "Second transaction",
        "Third transaction",
    ]
    
    for i, msg in enumerate(messages):
        with git_layer.begin(str(temp_repo_path), message=msg) as txn:
            txn.write_escalation_required()
            (Path(txn.path) / f"file{i}.txt").write_text(f"Content {i}")
    
    # Check Git log
    commits = list(repo.repo.iter_commits("main"))
    
    # Should have initial commit + merge commits for each transaction
    assert len(commits) >= len(messages)
    
    # Check commit messages
    commit_messages = [c.message.strip() for c in commits]
    for msg in messages:
        assert any(msg in cm for cm in commit_messages)


def test_concurrent_read_operations(temp_repo_path: Path):
    """Test concurrent read operations (should work fine)."""
    # Create initial data
    with git_layer.begin(str(temp_repo_path), message="Initial data") as txn:
        txn.write_escalation_required()
        (Path(txn.path) / "data.txt").write_text("shared data")
    
    # Concurrent reads
    def read_data():
        with git_layer.begin(str(temp_repo_path), message="Read only") as txn:
            # Don't escalate to write
            content = (Path(txn.path) / "data.txt").read_text()
            return content
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(read_data) for _ in range(3)]
        results = [f.result() for f in futures]
    
    # All should read the same data
    assert all(r == "shared data" for r in results)