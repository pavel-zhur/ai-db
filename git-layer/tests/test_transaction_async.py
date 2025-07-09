"""Async tests for Transaction class."""

from pathlib import Path

import pytest

import git_layer
from git_layer.exceptions import TransactionStateError
from git_layer.transaction import Transaction


@pytest.mark.asyncio
async def test_transaction_basic(temp_repo_path: Path):
    """Test basic transaction flow."""
    async with await git_layer.begin(str(temp_repo_path), message="Test transaction") as txn:
        assert txn.is_active
        assert txn.id
        assert txn.path == temp_repo_path

    # Transaction should be inactive after context exit
    assert not txn.is_active


@pytest.mark.asyncio
async def test_transaction_write_operations(temp_repo_path: Path, test_file_content: str):
    """Test transaction with write operations."""
    test_file = "data.yaml"

    async with await git_layer.begin(str(temp_repo_path), message="Add data") as txn:
        # Signal write escalation
        await txn.write_escalation_required()

        # Path should now be a clone
        assert txn.path != temp_repo_path
        assert "git-layer-" in str(txn.path)

        # Write file
        file_path = txn.path / test_file
        file_path.write_text(test_file_content)

        # File should exist in transaction
        assert file_path.exists()

    # After commit, file should exist in original repo
    assert (temp_repo_path / test_file).exists()
    assert (temp_repo_path / test_file).read_text() == test_file_content


@pytest.mark.asyncio
async def test_transaction_rollback(temp_repo_path: Path):
    """Test transaction rollback on exception."""
    test_file = "rollback.txt"

    with pytest.raises(ValueError):
        async with await git_layer.begin(str(temp_repo_path), message="Failing transaction") as txn:
            await txn.write_escalation_required()

            # Write file
            file_path = txn.path / test_file
            file_path.write_text("This should be rolled back")

            # Raise exception
            raise ValueError("Simulated error")

    # File should not exist in original repo
    assert not (temp_repo_path / test_file).exists()


@pytest.mark.asyncio
async def test_transaction_checkpoint(temp_repo_path: Path):
    """Test creating checkpoints during transaction."""
    async with await git_layer.begin(str(temp_repo_path), message="Checkpoint test") as txn:
        await txn.write_escalation_required()

        # First checkpoint
        (txn.path / "file1.txt").write_text("content1")
        await txn.checkpoint("Add file1")

        # Second checkpoint
        (txn.path / "file2.txt").write_text("content2")
        await txn.checkpoint("Add file2")

    # Both files should exist
    assert (temp_repo_path / "file1.txt").exists()
    assert (temp_repo_path / "file2.txt").exists()


@pytest.mark.asyncio
async def test_transaction_operation_complete(temp_repo_path: Path):
    """Test operation_complete method for ai-db integration."""
    async with await git_layer.begin(str(temp_repo_path), message="Operations test") as txn:
        await txn.write_escalation_required()

        # First operation
        (txn.path / "table1.yaml").write_text("id: 1\nname: test")
        await txn.operation_complete("Created table1")

        # Second operation
        (txn.path / "table2.yaml").write_text("id: 2\nname: test2")
        await txn.operation_complete("Created table2")

    # Both files should exist
    assert (temp_repo_path / "table1.yaml").exists()
    assert (temp_repo_path / "table2.yaml").exists()


@pytest.mark.asyncio
async def test_transaction_operation_failed(temp_repo_path: Path):
    """Test operation_failed method for ai-db integration."""
    async with await git_layer.begin(str(temp_repo_path), message="Failed operation test") as txn:
        await txn.write_escalation_required()

        # Create some data
        (txn.path / "data.yaml").write_text("test: data")

        # Simulate operation failure
        await txn.operation_failed("Simulated database constraint violation")

        # Transaction should still be active
        assert txn.is_active

    # Check that a failure branch was created
    from git_layer.repository import GitRepository

    repo = GitRepository(str(temp_repo_path))
    branches = await repo.get_branches()
    failure_branches = [b for b in branches if b.startswith("failed-transaction-")]
    assert len(failure_branches) > 0


@pytest.mark.asyncio
async def test_transaction_protocol_interface(temp_repo_path: Path):
    """Test that Transaction implements TransactionProtocol correctly."""
    from ai_shared.protocols import TransactionProtocol

    async with await git_layer.begin(str(temp_repo_path), message="Protocol test") as txn:
        # Check that it implements the protocol
        assert isinstance(txn, TransactionProtocol)

        # Check properties
        assert isinstance(txn.id, str)
        assert isinstance(txn.path, Path)

        # Check methods exist and are coroutines
        import inspect

        assert inspect.iscoroutinefunction(txn.write_escalation_required)
        assert inspect.iscoroutinefunction(txn.operation_complete)
        assert inspect.iscoroutinefunction(txn.operation_failed)


@pytest.mark.asyncio
async def test_transaction_no_writes(temp_repo_path: Path):
    """Test transaction with no write operations."""
    async with await git_layer.begin(str(temp_repo_path), message="Read-only transaction") as txn:
        # Don't call write_escalation_required
        assert txn.path == temp_repo_path

    # Should complete successfully without creating branches


@pytest.mark.asyncio
async def test_transaction_nested_error(temp_repo_path: Path):
    """Test that nested transactions are not allowed."""
    async with await git_layer.begin(str(temp_repo_path), message="Outer"):
        txn2 = Transaction(str(temp_repo_path), message="Inner")

        with pytest.raises(TransactionStateError, match="already active"):
            await txn2.begin()


@pytest.mark.asyncio
async def test_transaction_double_commit(temp_repo_path: Path):
    """Test that double commit raises error."""
    txn = Transaction(str(temp_repo_path), message="Test")
    await txn.begin()
    await txn.commit()

    with pytest.raises(TransactionStateError, match="already committed"):
        await txn.commit()


@pytest.mark.asyncio
async def test_transaction_operations_without_begin(temp_repo_path: Path):
    """Test that operations without begin raise errors."""
    txn = Transaction(str(temp_repo_path), message="Test")

    with pytest.raises(TransactionStateError, match="No active transaction"):
        await txn.write_escalation_required()

    with pytest.raises(TransactionStateError, match="No active transaction"):
        await txn.checkpoint()

    with pytest.raises(TransactionStateError, match="No active transaction"):
        await txn.commit()


@pytest.mark.asyncio
async def test_transaction_multiple_files(temp_repo_path: Path):
    """Test transaction with multiple file operations."""
    files = {
        "config.yaml": "setting: value",
        "data/users.yaml": "- name: Alice\n- name: Bob",
        "data/products.yaml": "- id: 1\n  name: Product A",
    }

    async with await git_layer.begin(str(temp_repo_path), message="Add multiple files") as txn:
        await txn.write_escalation_required()

        for file_path, content in files.items():
            full_path = txn.path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

    # All files should exist
    for file_path, content in files.items():
        assert (temp_repo_path / file_path).exists()
        assert (temp_repo_path / file_path).read_text() == content


@pytest.mark.asyncio
async def test_transaction_modify_existing(temp_repo_path: Path):
    """Test modifying existing files in a transaction."""
    # Create initial file
    existing_file = temp_repo_path / "existing.txt"
    existing_file.write_text("original content")

    # Commit it
    from git_layer.repository import GitRepository

    repo = GitRepository(str(temp_repo_path))
    await repo.commit_all("Add existing file")

    # Modify in transaction
    async with await git_layer.begin(str(temp_repo_path), message="Modify existing") as txn:
        await txn.write_escalation_required()

        file_path = txn.path / "existing.txt"
        file_path.write_text("modified content")

    # Should have new content
    assert existing_file.read_text() == "modified content"


@pytest.mark.asyncio
async def test_transaction_recovery_after_crash(temp_repo_path: Path):
    """Test recovery after simulated crash."""
    # Start a transaction and simulate crash
    txn = Transaction(str(temp_repo_path), message="Crashed transaction")
    await txn.begin()
    await txn.write_escalation_required()

    # Write some data
    (txn.path / "crash.txt").write_text("crashed data")

    # Simulate crash - don't call commit or rollback
    del txn

    # Recover the repository (would be done by recovery process)
    await git_layer.recover(str(temp_repo_path))

    # Create new transaction - should work
    async with await git_layer.begin(str(temp_repo_path), message="After crash") as txn2:
        await txn2.write_escalation_required()
        (txn2.path / "recovered.txt").write_text("recovered")

    # Only recovered file should exist
    assert not (temp_repo_path / "crash.txt").exists()
    assert (temp_repo_path / "recovered.txt").exists()


@pytest.mark.asyncio
async def test_recover_function(temp_repo_path: Path):
    """Test the recover function."""
    # Create some mess
    from git_layer.repository import GitRepository

    repo = GitRepository(str(temp_repo_path))

    # Create some transaction branches
    await repo.create_branch("transaction-abc123-20240101-120000")
    await repo.create_branch("transaction-def456-20240101-130000")

    # Run recover
    await git_layer.recover(str(temp_repo_path))

    # Should be on main branch
    assert repo.repo.active_branch.name == "main"
