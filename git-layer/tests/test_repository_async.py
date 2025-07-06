"""Async tests for GitRepository class."""

import pytest
from pathlib import Path

from git_layer.repository import GitRepository
from git_layer.exceptions import RepositoryError, GitOperationError


@pytest.mark.asyncio
async def test_repository_init(temp_repo_path: Path):
    """Test repository initialization."""
    repo = GitRepository(str(temp_repo_path))
    
    # Should have created .git directory
    assert (temp_repo_path / ".git").exists()
    
    # Should have main branch
    branches = await repo.get_branches()
    assert "main" in branches
    
    # Should have initial commit
    assert repo.repo.head.commit


@pytest.mark.asyncio
async def test_ensure_clean_working_tree(temp_repo_path: Path):
    """Test clean working tree check."""
    repo = GitRepository(str(temp_repo_path))
    
    # Should be clean initially
    await repo.ensure_clean_working_tree()
    
    # Create uncommitted file
    (temp_repo_path / "uncommitted.txt").write_text("test")
    
    # Should raise error
    with pytest.raises(RepositoryError, match="uncommitted changes"):
        await repo.ensure_clean_working_tree()


@pytest.mark.asyncio
async def test_create_and_checkout_branch(temp_repo_path: Path):
    """Test branch creation and checkout."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create branch
    branch_name = "test-branch"
    await repo.create_branch(branch_name)
    
    # Should exist
    assert await repo.branch_exists(branch_name)
    
    # Checkout branch
    await repo.checkout_branch(branch_name)
    assert repo.repo.active_branch.name == branch_name


@pytest.mark.asyncio
async def test_commit_all(temp_repo_path: Path):
    """Test committing all changes."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create files
    (temp_repo_path / "file1.txt").write_text("content1")
    (temp_repo_path / "file2.txt").write_text("content2")
    
    # Commit
    sha = await repo.commit_all("Add test files")
    assert sha
    
    # Files should be committed
    await repo.ensure_clean_working_tree()


@pytest.mark.asyncio
async def test_merge_branch(temp_repo_path: Path):
    """Test branch merging."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create and checkout feature branch
    feature_branch = "feature-test"
    await repo.create_branch(feature_branch)
    await repo.checkout_branch(feature_branch)
    
    # Add file in feature branch
    (temp_repo_path / "feature.txt").write_text("feature content")
    await repo.commit_all("Add feature")
    
    # Merge to main
    await repo.merge_branch(feature_branch, "Merge feature branch")
    
    # Should be on main
    assert repo.repo.active_branch.name == "main"
    
    # File should exist on main
    assert (temp_repo_path / "feature.txt").exists()


@pytest.mark.asyncio
async def test_delete_branch(temp_repo_path: Path):
    """Test branch deletion."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create branch
    branch_name = "to-delete"
    await repo.create_branch(branch_name)
    assert await repo.branch_exists(branch_name)
    
    # Delete branch
    await repo.delete_branch(branch_name)
    assert not await repo.branch_exists(branch_name)


@pytest.mark.asyncio
async def test_reset_to_main(temp_repo_path: Path):
    """Test resetting to main branch."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create branch and make changes
    await repo.create_branch("temp-branch")
    await repo.checkout_branch("temp-branch")
    (temp_repo_path / "temp.txt").write_text("temporary")
    
    # Reset to main
    await repo.reset_to_main()
    
    # Should be on main
    assert repo.repo.active_branch.name == "main"
    
    # Temp file should not exist
    assert not (temp_repo_path / "temp.txt").exists()


@pytest.mark.asyncio
async def test_clone_to_temp(temp_repo_path: Path):
    """Test creating temporary clone."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create some content
    (temp_repo_path / "original.txt").write_text("original content")
    await repo.commit_all("Add original file")
    
    # Clone
    clone = await repo.clone_to_temp()
    
    try:
        # Clone should have the file
        assert (clone.path / "original.txt").exists()
        assert (clone.path / "original.txt").read_text() == "original content"
        
        # Clone path should be temporary
        assert "git-layer-" in str(clone.path)
        
        # Cleanup
        await clone.cleanup_clone()
        assert not clone.path.exists()
    finally:
        # Ensure cleanup even on failure
        if clone.path.exists():
            await clone.cleanup_clone()


@pytest.mark.asyncio
async def test_recover_to_clean_state(temp_repo_path: Path):
    """Test repository recovery."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create some transaction branches
    await repo.create_branch("transaction-abc123-20240101-120000")
    await repo.create_branch("transaction-def456-20240101-130000")
    
    # Switch to one of them
    await repo.checkout_branch("transaction-abc123-20240101-120000")
    
    # Add uncommitted changes
    (temp_repo_path / "uncommitted.txt").write_text("test")
    
    # Recover
    await repo.recover_to_clean_state()
    
    # Should be on main with clean working tree
    assert repo.repo.active_branch.name == "main"
    await repo.ensure_clean_working_tree()


@pytest.mark.asyncio
async def test_repository_error_handling(temp_repo_path: Path):
    """Test error handling in repository operations."""
    repo = GitRepository(str(temp_repo_path))
    
    # Try to checkout non-existent branch
    with pytest.raises(GitOperationError, match="Failed to checkout"):
        await repo.checkout_branch("non-existent")
    
    # Try to merge non-existent branch
    with pytest.raises(GitOperationError, match="Failed to merge"):
        await repo.merge_branch("non-existent", "Test merge")