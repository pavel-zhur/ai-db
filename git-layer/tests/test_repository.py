"""Tests for GitRepository class."""

import pytest
from pathlib import Path

from git_layer.repository import GitRepository
from git_layer.exceptions import RepositoryError, GitOperationError


def test_repository_init_new(temp_repo_path: Path):
    """Test initializing a new repository."""
    repo = GitRepository(str(temp_repo_path))
    
    assert repo.path == temp_repo_path
    assert (temp_repo_path / ".git").exists()
    assert (temp_repo_path / ".gitignore").exists()
    
    # Should have main branch
    branches = repo.get_branches()
    assert "main" in branches


def test_repository_init_existing(temp_repo_path: Path):
    """Test initializing an existing repository."""
    # Create repo first
    repo1 = GitRepository(str(temp_repo_path))
    
    # Create a test file
    test_file = temp_repo_path / "test.txt"
    test_file.write_text("test content")
    repo1.commit_all("Add test file")
    
    # Initialize again
    repo2 = GitRepository(str(temp_repo_path))
    assert repo2.path == temp_repo_path
    assert test_file.exists()


def test_repository_clean_check(temp_repo_path: Path):
    """Test checking for clean working tree."""
    repo = GitRepository(str(temp_repo_path))
    
    # Should be clean initially
    repo.ensure_clean_working_tree()  # Should not raise
    
    # Create uncommitted file
    test_file = temp_repo_path / "uncommitted.txt"
    test_file.write_text("uncommitted content")
    
    # Should raise error
    with pytest.raises(RepositoryError, match="uncommitted changes"):
        repo.ensure_clean_working_tree()


def test_repository_branch_operations(temp_repo_path: Path):
    """Test branch creation and management."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create a branch
    branch = repo.create_branch("test-branch")
    assert branch.name == "test-branch"
    assert repo.branch_exists("test-branch")
    
    # Checkout branch
    repo.checkout_branch("test-branch")
    assert repo.repo.active_branch.name == "test-branch"
    
    # Delete branch (need to switch back to main first)
    repo.checkout_branch("main")
    repo.delete_branch("test-branch")
    assert not repo.branch_exists("test-branch")


def test_repository_commit(temp_repo_path: Path):
    """Test committing changes."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create files
    (temp_repo_path / "file1.txt").write_text("content1")
    (temp_repo_path / "file2.txt").write_text("content2")
    
    # Commit
    sha = repo.commit_all("Test commit")
    assert len(sha) == 40  # SHA should be 40 chars
    
    # Files should be committed
    assert not repo.repo.is_dirty()
    
    # No changes, should return current SHA
    sha2 = repo.commit_all("No changes")
    assert sha2 == sha


def test_repository_merge(temp_repo_path: Path):
    """Test merging branches."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create and checkout feature branch
    repo.create_branch("feature")
    repo.checkout_branch("feature")
    
    # Make changes
    (temp_repo_path / "feature.txt").write_text("feature content")
    repo.commit_all("Add feature")
    
    # Merge to main
    repo.merge_branch("feature", "Merge feature branch")
    
    # Check file exists on main
    assert repo.repo.active_branch.name == "main"
    assert (temp_repo_path / "feature.txt").exists()


def test_repository_clone(temp_repo_path: Path):
    """Test cloning repository."""
    repo = GitRepository(str(temp_repo_path))
    
    # Add some content
    (temp_repo_path / "original.txt").write_text("original content")
    repo.commit_all("Add original file")
    
    # Clone
    cloned_repo = repo.clone_to_temp()
    
    try:
        # Check clone
        assert cloned_repo.path != repo.path
        assert "git-layer-" in str(cloned_repo.path)
        assert (cloned_repo.path / "original.txt").exists()
        
        # Modify in clone
        (cloned_repo.path / "cloned.txt").write_text("cloned content")
        cloned_repo.commit_all("Add cloned file")
        
        # Original should not have the file
        assert not (temp_repo_path / "cloned.txt").exists()
        
    finally:
        # Cleanup
        cloned_repo.cleanup_clone()
        assert not cloned_repo.path.exists()


def test_repository_reset(temp_repo_path: Path):
    """Test resetting to main."""
    repo = GitRepository(str(temp_repo_path))
    
    # Make changes
    (temp_repo_path / "test.txt").write_text("test")
    
    # Reset
    repo.reset_to_main()
    
    # Changes should be gone
    assert not (temp_repo_path / "test.txt").exists()
    assert not repo.repo.is_dirty()


def test_repository_recovery(temp_repo_path: Path):
    """Test recovery to clean state."""
    repo = GitRepository(str(temp_repo_path))
    
    # Create some transaction branches
    repo.create_branch("transaction-old-12345678")
    repo.create_branch("transaction-new-87654321")
    
    # Make some uncommitted changes
    (temp_repo_path / "dirty.txt").write_text("dirty")
    
    # Recover
    repo.recover_to_clean_state()
    
    # Should be on main with no uncommitted changes
    assert repo.repo.active_branch.name == "main"
    assert not repo.repo.is_dirty()
    assert not (temp_repo_path / "dirty.txt").exists()