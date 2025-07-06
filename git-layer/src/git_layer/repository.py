"""Git repository operations wrapper."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from git import Head, Repo

from .exceptions import GitOperationError, RepositoryError
from .utils import cleanup_old_transaction_branches, ensure_git_user_config

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
                if not self.repo.heads:
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
            # Create a basic .gitignore file
            gitignore_path = self._path / ".gitignore"
            gitignore_path.write_text("*.pyc\n__pycache__/\n.DS_Store\n")

            self.repo.index.add([str(gitignore_path)])
            self.repo.index.commit("Initial commit")

            # Ensure we're on main branch
            if not self.repo.heads:
                # No branches exist yet, create main
                self.repo.create_head("main")

            # Check if we need to switch to main
            if hasattr(self.repo, "active_branch") and self.repo.active_branch.name != "main":
                if "main" in [h.name for h in self.repo.heads]:
                    self.repo.heads.main.checkout()
                else:
                    # Rename master to main if it exists
                    if "master" in [h.name for h in self.repo.heads]:
                        self.repo.heads.master.rename("main")
            elif not hasattr(self.repo, "active_branch"):
                # No active branch, checkout main
                if "main" in [h.name for h in self.repo.heads]:
                    self.repo.heads.main.checkout()
                elif "master" in [h.name for h in self.repo.heads]:
                    self.repo.heads.master.rename("main")
                    self.repo.heads.main.checkout()

        except Exception as e:
            raise GitOperationError("Failed to create initial commit", e)

    async def ensure_clean_working_tree(self) -> None:
        """Ensure the working tree has no uncommitted changes."""
        is_dirty = await asyncio.to_thread(self.repo.is_dirty, untracked_files=True)
        if is_dirty:
            raise RepositoryError(
                "Working tree has uncommitted changes. "
                "Please commit or stash changes before starting a transaction."
            )

    async def create_branch(self, branch_name: str) -> Head:
        """Create a new branch from the current HEAD.

        Args:
            branch_name: Name of the branch to create

        Returns:
            The created branch
        """
        try:
            branch = await asyncio.to_thread(self.repo.create_head, branch_name)
            logger.info(f"Created branch: {branch_name}")
            return branch
        except Exception as e:
            raise GitOperationError(f"Failed to create branch {branch_name}", e)

    async def checkout_branch(self, branch_name: str) -> None:
        """Checkout the specified branch.

        Args:
            branch_name: Name of the branch to checkout
        """
        try:
            await asyncio.to_thread(self.repo.heads[branch_name].checkout)
            logger.info(f"Checked out branch: {branch_name}")
        except Exception as e:
            raise GitOperationError(f"Failed to checkout branch {branch_name}", e)

    async def commit_all(self, message: str) -> str:
        """Stage all changes and create a commit.

        Args:
            message: Commit message

        Returns:
            The commit SHA
        """
        try:
            # Stage all changes (including untracked files)
            await asyncio.to_thread(self.repo.git.add, A=True)

            # Only commit if there are changes
            is_dirty = await asyncio.to_thread(self.repo.is_dirty)
            if is_dirty:
                commit = await asyncio.to_thread(self.repo.index.commit, message)
                logger.info(f"Created commit: {commit.hexsha[:8]} - {message}")
                return commit.hexsha
            else:
                logger.debug("No changes to commit")
                return self.repo.head.commit.hexsha

        except Exception as e:
            raise GitOperationError(f"Failed to commit: {message}", e)

    async def merge_branch(self, branch_name: str, message: str) -> None:
        """Merge the specified branch into the current branch.

        Args:
            branch_name: Name of the branch to merge
            message: Merge commit message
        """
        try:
            # Ensure we're on main
            await self.checkout_branch("main")

            # Use git merge command for proper merge
            await asyncio.to_thread(self.repo.git.merge, branch_name, m=message)

            logger.info(f"Merged branch {branch_name} into main")

        except Exception as e:
            raise GitOperationError(f"Failed to merge branch {branch_name}", e)

    async def delete_branch(self, branch_name: str) -> None:
        """Delete the specified branch.

        Args:
            branch_name: Name of the branch to delete
        """
        try:
            await asyncio.to_thread(self.repo.delete_head, branch_name, force=True)
            logger.info(f"Deleted branch: {branch_name}")
        except Exception as e:
            # Branch might not exist, which is okay
            logger.warning(f"Could not delete branch {branch_name}: {e}")

    async def reset_to_main(self) -> None:
        """Reset the repository to the main branch, discarding any changes."""
        try:
            await self.checkout_branch("main")
            await asyncio.to_thread(self.repo.head.reset, index=True, working_tree=True)
            # Clean any untracked files
            await asyncio.to_thread(self.repo.git.clean, "-fd")
            logger.info("Reset to main branch")
        except Exception as e:
            raise GitOperationError("Failed to reset to main", e)

    async def clone_to_temp(self) -> "GitRepository":
        """Create a temporary clone of the repository.

        Returns:
            A new GitRepository instance pointing to the clone
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="git-layer-")
            logger.info(f"Creating temporary clone in: {temp_dir}")

            # Clone the repository
            cloned_repo = await asyncio.to_thread(self.repo.clone, temp_dir)

            # Fetch all remote branches
            for remote in cloned_repo.remotes:
                await asyncio.to_thread(remote.fetch)

            # Create local tracking branches for all remote branches
            origin = cloned_repo.remotes.origin
            for ref in origin.refs:
                # Skip HEAD reference
                if ref.name == "origin/HEAD":
                    continue

                # Extract branch name (remove 'origin/' prefix)
                branch_name = ref.name.split("/")[-1]

                # Skip if branch already exists locally
                if branch_name in [h.name for h in cloned_repo.heads]:
                    continue

                # Create local branch tracking the remote
                await asyncio.to_thread(cloned_repo.create_head, branch_name, ref)

            # Return a new GitRepository instance
            return GitRepository(temp_dir)

        except Exception as e:
            raise GitOperationError("Failed to create temporary clone", e)

    async def cleanup_clone(self) -> None:
        """Remove a temporary clone directory."""
        if "git-layer-" in str(self._path):
            try:
                await asyncio.to_thread(shutil.rmtree, self._path)
                logger.info(f"Cleaned up temporary clone: {self._path}")
            except Exception as e:
                logger.error(f"Failed to cleanup clone: {e}")

    async def get_branches(self) -> List[str]:
        """Get a list of all branch names."""
        heads = await asyncio.to_thread(lambda: list(self.repo.heads))
        return [head.name for head in heads]

    async def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        branches = await self.get_branches()
        return branch_name in branches

    async def recover_to_clean_state(self) -> None:
        """Recover the repository to a clean state on main branch.

        This is used for crash recovery and ensures the repository
        is in a consistent state.
        """
        try:
            # First, try to clean up any locks
            index_lock = self._path / ".git" / "index.lock"
            if index_lock.exists():
                await asyncio.to_thread(index_lock.unlink)
                logger.warning("Removed stale Git index lock")

            # Clean up write lock
            write_lock = self._path / ".git" / "ai-db-write.lock"
            if write_lock.exists():
                await asyncio.to_thread(write_lock.unlink)
                logger.warning("Removed stale write lock")

            # Reset to main branch
            heads = await asyncio.to_thread(lambda: list(self.repo.heads))
            if "main" in [h.name for h in heads]:
                await asyncio.to_thread(self.repo.heads.main.checkout, force=True)
                await asyncio.to_thread(self.repo.head.reset, index=True, working_tree=True)
                # Clean any untracked files
                await asyncio.to_thread(self.repo.git.clean, "-fd")
            else:
                # Main doesn't exist, this is a serious problem
                raise RepositoryError("Main branch does not exist")

            # Clean up old transaction branches
            deleted = await asyncio.to_thread(
                cleanup_old_transaction_branches, self.repo, keep_hours=24
            )
            if deleted:
                logger.info(f"Cleaned up {len(deleted)} old transaction branches")

            # Clear transaction tracking
            from .transaction import Transaction

            repo_path = str(self._path)
            if repo_path in Transaction._active_transactions:
                del Transaction._active_transactions[repo_path]
                logger.info("Cleared stale transaction tracking")

        except Exception as e:
            raise GitOperationError(f"Failed to recover repository: {e}", e)
