"""Git repository operations wrapper."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
from uuid import uuid4

import git
from git import Repo, Head

from .exceptions import RepositoryError, GitOperationError
from .utils import ensure_git_user_config, cleanup_old_transaction_branches

logger = logging.getLogger(__name__)


class GitRepository:
    """Wrapper for Git repository operations."""
    
    def __init__(self, path: str):
        """Initialize repository at the given path.
        
        Args:
            path: Path to the Git repository. Will be created if it doesn't exist.
        """
        self._path = Path(path).resolve()
        self._repo: Optional[Repo] = None
        self._init_repository()
    
    @property
    def path(self) -> Path:
        """Get the repository path."""
        return self._path
    
    @property
    def repo(self) -> Repo:
        """Get the GitPython repository object."""
        if self._repo is None:
            raise RepositoryError("Repository not initialized")
        return self._repo
    
    def _init_repository(self) -> None:
        """Initialize the repository, creating it if necessary."""
        try:
            if not self._path.exists():
                logger.info(f"Creating directory: {self._path}")
                self._path.mkdir(parents=True, exist_ok=True)
            
            if not (self._path / ".git").exists():
                logger.info(f"Initializing Git repository: {self._path}")
                self._repo = Repo.init(self._path)
                
                # Ensure git user config is set
                ensure_git_user_config(self._repo)
                
                # Create initial commit if repository is empty
                if not self._repo.heads:
                    self._create_initial_commit()
            else:
                self._repo = Repo(self._path)
                
                # Ensure git user config is set
                ensure_git_user_config(self._repo)
                
        except Exception as e:
            raise RepositoryError(f"Failed to initialize repository: {e}") from e
    
    def _create_initial_commit(self) -> None:
        """Create an initial commit to establish the main branch."""
        try:
            # Create a .gitignore file
            gitignore_path = self._path / ".gitignore"
            gitignore_path.write_text("*.pyc\n__pycache__/\n.DS_Store\n")
            
            self._repo.index.add([str(gitignore_path)])
            self._repo.index.commit("Initial commit")
            
            # Ensure we're on main branch
            if not self._repo.heads:
                # No branches exist yet, create main
                self._repo.create_head("main")
            
            # Check if we need to switch to main
            if hasattr(self._repo, 'active_branch') and self._repo.active_branch.name != "main":
                self._repo.heads.main.checkout()
            elif not hasattr(self._repo, 'active_branch'):
                # No active branch, checkout main
                self._repo.heads.main.checkout()
                
        except Exception as e:
            raise GitOperationError("Failed to create initial commit", e)
    
    def ensure_clean_working_tree(self) -> None:
        """Ensure the working tree has no uncommitted changes."""
        if self._repo.is_dirty(untracked_files=True):
            raise RepositoryError(
                "Working tree has uncommitted changes. "
                "Please commit or stash changes before starting a transaction."
            )
    
    def create_branch(self, branch_name: str) -> Head:
        """Create a new branch from the current HEAD.
        
        Args:
            branch_name: Name of the branch to create
            
        Returns:
            The created branch
        """
        try:
            branch = self._repo.create_head(branch_name)
            logger.info(f"Created branch: {branch_name}")
            return branch
        except Exception as e:
            raise GitOperationError(f"Failed to create branch {branch_name}", e)
    
    def checkout_branch(self, branch_name: str) -> None:
        """Checkout the specified branch.
        
        Args:
            branch_name: Name of the branch to checkout
        """
        try:
            self._repo.heads[branch_name].checkout()
            logger.info(f"Checked out branch: {branch_name}")
        except Exception as e:
            raise GitOperationError(f"Failed to checkout branch {branch_name}", e)
    
    def commit_all(self, message: str) -> str:
        """Stage all changes and create a commit.
        
        Args:
            message: Commit message
            
        Returns:
            The commit SHA
        """
        try:
            # Stage all changes (including untracked files)
            self._repo.git.add(A=True)
            
            # Only commit if there are changes
            if self._repo.is_dirty():
                commit = self._repo.index.commit(message)
                logger.info(f"Created commit: {commit.hexsha[:8]} - {message}")
                return commit.hexsha
            else:
                logger.debug("No changes to commit")
                return self._repo.head.commit.hexsha
                
        except Exception as e:
            raise GitOperationError(f"Failed to commit: {message}", e)
    
    def merge_branch(self, branch_name: str, message: str) -> None:
        """Merge the specified branch into the current branch.
        
        Args:
            branch_name: Name of the branch to merge
            message: Merge commit message
        """
        try:
            # Ensure we're on main
            self.checkout_branch("main")
            
            # Merge the branch
            merge_base = self._repo.merge_base("main", branch_name)
            self._repo.index.merge_tree(self._repo.heads[branch_name])
            self._repo.index.commit(message, parent_commits=(self._repo.head.commit, self._repo.heads[branch_name].commit))
            
            logger.info(f"Merged branch {branch_name} into main")
            
        except Exception as e:
            raise GitOperationError(f"Failed to merge branch {branch_name}", e)
    
    def delete_branch(self, branch_name: str) -> None:
        """Delete the specified branch.
        
        Args:
            branch_name: Name of the branch to delete
        """
        try:
            self._repo.delete_head(branch_name, force=True)
            logger.info(f"Deleted branch: {branch_name}")
        except Exception as e:
            # Branch might not exist, which is okay
            logger.warning(f"Could not delete branch {branch_name}: {e}")
    
    def reset_to_main(self) -> None:
        """Reset the repository to the main branch, discarding any changes."""
        try:
            self.checkout_branch("main")
            self._repo.head.reset(index=True, working_tree=True)
            logger.info("Reset to main branch")
        except Exception as e:
            raise GitOperationError("Failed to reset to main", e)
    
    def clone_to_temp(self) -> "GitRepository":
        """Create a temporary clone of the repository.
        
        Returns:
            A new GitRepository instance pointing to the clone
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="git-layer-")
            logger.info(f"Creating temporary clone in: {temp_dir}")
            
            # Clone the repository
            cloned_repo = self._repo.clone(temp_dir)
            
            # Return a new GitRepository instance
            return GitRepository(temp_dir)
            
        except Exception as e:
            raise GitOperationError("Failed to create temporary clone", e)
    
    def cleanup_clone(self) -> None:
        """Remove a temporary clone directory."""
        if "git-layer-" in str(self._path):
            try:
                shutil.rmtree(self._path)
                logger.info(f"Cleaned up temporary clone: {self._path}")
            except Exception as e:
                logger.error(f"Failed to cleanup clone: {e}")
    
    def get_branches(self) -> List[str]:
        """Get a list of all branch names."""
        return [head.name for head in self._repo.heads]
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        return branch_name in [h.name for h in self._repo.heads]
    
    def recover_to_clean_state(self) -> None:
        """Recover the repository to a clean state on main branch.
        
        This is used for crash recovery and ensures the repository
        is in a consistent state.
        """
        try:
            # First, try to clean up any locks
            lock_file = self._path / ".git" / "index.lock"
            if lock_file.exists():
                lock_file.unlink()
                logger.warning("Removed stale Git index lock")
            
            # Reset to main branch
            if "main" in [h.name for h in self._repo.heads]:
                self._repo.heads.main.checkout(force=True)
                self._repo.head.reset(index=True, working_tree=True)
            else:
                # Main doesn't exist, this is a serious problem
                raise RepositoryError("Main branch does not exist")
            
            # Clean up old transaction branches
            deleted = cleanup_old_transaction_branches(self._repo, keep_hours=24)
            if deleted:
                logger.info(f"Cleaned up {len(deleted)} old transaction branches")
                
        except Exception as e:
            raise GitOperationError(f"Failed to recover repository: {e}", e)