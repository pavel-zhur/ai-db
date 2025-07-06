"""Transaction management for git-layer."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from ai_shared.protocols import TransactionProtocol

from .exceptions import TransactionError, TransactionStateError
from .repository import GitRepository

logger = logging.getLogger(__name__)


class Transaction(TransactionProtocol):
    """Manages a Git-based transaction with BEGIN/COMMIT/ROLLBACK semantics."""

    # Track active transactions per repository
    _active_transactions: dict[str, str] = {}

    def __init__(self, repo_path: str, message: Optional[str] = None):
        """Initialize a new transaction.

        Args:
            repo_path: Path to the Git repository
            message: Optional transaction message for commits
        """
        self._original_repo = GitRepository(repo_path)
        self._working_repo: Optional[GitRepository] = None
        self._transaction_id = uuid4().hex[:8]
        self._timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._branch_name = f"transaction-{self._transaction_id}-{self._timestamp}"
        self._message = message or f"Transaction {self._transaction_id}"
        self._active = False
        self._write_escalated = False
        self._committed = False

    @property
    def path(self) -> Path:
        """Get the current working directory path.

        Returns:
            Path to the repository (original or clone)
        """
        if self._working_repo:
            return self._working_repo.path
        return self._original_repo.path

    @property
    def id(self) -> str:
        """Get the transaction ID."""
        return self._transaction_id

    @property
    def transaction_id(self) -> str:
        """Get the transaction ID (deprecated, use id property)."""
        return self._transaction_id

    @property
    def is_active(self) -> bool:
        """Check if the transaction is active."""
        return self._active

    async def __aenter__(self) -> "Transaction":
        """Begin the transaction."""
        await self.begin()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End the transaction, committing on success or rolling back on failure."""
        if exc_type is None:
            try:
                await self.commit()
            except Exception:
                logger.exception("Failed to commit transaction")
                await self.rollback()
                raise
        else:
            logger.info(f"Transaction failed with {exc_type.__name__}: {exc_val}")
            await self.rollback()

    def __del__(self) -> None:
        """Cleanup transaction if it wasn't properly closed."""
        if self._active:
            logger.warning(f"Transaction {self._transaction_id} was not properly closed")
            # Clear from active transactions
            repo_path = str(self._original_repo.path)
            if repo_path in Transaction._active_transactions:
                del Transaction._active_transactions[repo_path]
            # Cannot call async rollback in destructor

    async def begin(self) -> None:
        """Begin a new transaction by creating a branch."""
        if self._active:
            raise TransactionStateError("Transaction already active")

        # Check for nested transactions
        repo_path = str(self._original_repo.path)
        if repo_path in Transaction._active_transactions:
            active_txn = Transaction._active_transactions[repo_path]
            raise TransactionStateError(f"Transaction {active_txn} already active on repository")

        try:
            # Ensure main branch is clean
            await self._original_repo.ensure_clean_working_tree()

            # Create transaction branch
            await self._original_repo.create_branch(self._branch_name)

            self._active = True
            Transaction._active_transactions[repo_path] = self._transaction_id
            logger.info(f"Transaction {self._transaction_id} started")

        except Exception as e:
            raise TransactionError(f"Failed to begin transaction: {e}") from e

    async def _acquire_write_lock(self) -> None:
        """Acquire write lock to prevent concurrent write transactions."""
        lock_file = self._original_repo.path / ".git" / "ai-db-write.lock"
        try:
            # Check if lock exists
            if lock_file.exists():
                raise TransactionError("Another write transaction in progress")

            # Create lock file
            lock_file.write_text(self._transaction_id)
            logger.info(f"Acquired write lock for transaction {self._transaction_id}")
        except Exception as e:
            raise TransactionError(f"Failed to acquire write lock: {e}") from e

    async def _release_write_lock(self) -> None:
        """Release write lock."""
        lock_file = self._original_repo.path / ".git" / "ai-db-write.lock"
        try:
            if lock_file.exists():
                lock_file.unlink()
                logger.info(f"Released write lock for transaction {self._transaction_id}")
        except Exception as e:
            logger.warning(f"Failed to release write lock: {e}")

    async def _escalate_to_write(self) -> None:
        """Escalate to write mode by creating a temporary clone."""
        if self._write_escalated:
            return

        try:
            # Acquire write lock
            await self._acquire_write_lock()

            logger.info(f"Escalating transaction {self._transaction_id} to write mode")

            # Create a temporary clone
            self._working_repo = await self._original_repo.clone_to_temp()

            # Checkout the transaction branch in the clone
            await self._working_repo.checkout_branch(self._branch_name)

            self._write_escalated = True

        except Exception as e:
            raise TransactionError(f"Failed to escalate to write mode: {e}") from e

    async def _detect_write_operation(self) -> None:
        """Check if any files have been modified and escalate if needed."""
        if not self._active:
            return

        # For now, we'll rely on the client to trigger write escalation
        # by accessing the path property after making changes
        # In a more sophisticated implementation, we could monitor file changes
        pass

    async def checkpoint(self, message: Optional[str] = None) -> None:
        """Create a checkpoint commit for the current state.

        Args:
            message: Optional commit message
        """
        if not self._active:
            raise TransactionStateError("No active transaction")

        if not self._write_escalated:
            # No writes have occurred yet
            return

        commit_message = message or f"Transaction {self._transaction_id}: checkpoint"

        try:
            if self._working_repo:
                await self._working_repo.commit_all(commit_message)
        except Exception as e:
            raise TransactionError(f"Failed to create checkpoint: {e}") from e

    async def commit(self) -> None:
        """Commit the transaction by merging to main."""
        if self._committed:
            raise TransactionStateError("Transaction already committed")

        if not self._active:
            raise TransactionStateError("No active transaction")

        try:
            if self._write_escalated:
                # Commit any pending changes
                await self.checkpoint("Final checkpoint before merge")

                # Push changes back to original repo
                # We need to fetch from the clone to the original
                # Add the working repo as a remote to the original
                remote_name = f"clone_{self._transaction_id}"
                try:
                    # Add remote to original repo pointing to clone
                    if self._working_repo is None:
                        raise TransactionError("Working repository not initialized")

                    remote = await asyncio.to_thread(
                        self._original_repo.repo.create_remote,
                        remote_name,
                        str(self._working_repo.path),
                    )

                    # Fetch the transaction branch from clone
                    await asyncio.to_thread(
                        remote.fetch, refspec=f"{self._branch_name}:{self._branch_name}", force=True
                    )

                    # Remove the temporary remote
                    await asyncio.to_thread(self._original_repo.repo.delete_remote, remote)
                except Exception:
                    # Try to clean up remote if it exists
                    try:
                        if remote_name in [r.name for r in self._original_repo.repo.remotes]:
                            remote = self._original_repo.repo.remotes[remote_name]
                            await asyncio.to_thread(self._original_repo.repo.delete_remote, remote)
                    except Exception:
                        pass
                    raise

                # Merge to main in the original repo
                merge_message = f"Transaction {self._transaction_id}: {self._message}"
                await self._original_repo.merge_branch(self._branch_name, merge_message)

                # Cleanup the clone
                if self._working_repo is not None:
                    await self._working_repo.cleanup_clone()
                    self._working_repo = None

                # Release write lock
                await self._release_write_lock()
            else:
                # No writes occurred, just merge the empty branch to main
                # Actually, no need to merge if no changes were made
                logger.info("No changes in transaction, skipping merge")

            # Delete the transaction branch
            await self._original_repo.delete_branch(self._branch_name)

            self._committed = True
            self._active = False

            # Remove from active transactions
            repo_path = str(self._original_repo.path)
            if repo_path in Transaction._active_transactions:
                del Transaction._active_transactions[repo_path]

            logger.info(f"Transaction {self._transaction_id} committed")

        except Exception as e:
            raise TransactionError(f"Failed to commit transaction: {e}") from e

    async def rollback(self) -> None:
        """Rollback the transaction by abandoning the branch."""
        if not self._active:
            return  # Already rolled back or not started

        try:
            if self._write_escalated and self._working_repo:
                # Commit current state to the branch for debugging
                try:
                    await self.checkpoint("Rollback checkpoint")

                    # Push the rollback state back to original repo
                    remote_name = f"clone_{self._transaction_id}"
                    try:
                        if self._working_repo is None:
                            raise TransactionError("Working repository not initialized")

                        remote = await asyncio.to_thread(
                            self._original_repo.repo.create_remote,
                            remote_name,
                            str(self._working_repo.path),
                        )
                        await asyncio.to_thread(
                            remote.fetch,
                            refspec=f"{self._branch_name}:{self._branch_name}",
                            force=True,
                        )
                        await asyncio.to_thread(self._original_repo.repo.delete_remote, remote)
                    except Exception:
                        logger.warning("Could not push rollback state to original repo")
                except Exception:
                    logger.warning("Could not create rollback checkpoint")

                # Cleanup the clone
                if self._working_repo is not None:
                    await self._working_repo.cleanup_clone()
                    self._working_repo = None

                # Release write lock
                await self._release_write_lock()

            # Return to main branch in original repo
            await self._original_repo.reset_to_main()

            # Note: We keep the transaction branch for debugging
            # In production, you might want to delete it after some time

            self._active = False

            # Remove from active transactions
            repo_path = str(self._original_repo.path)
            if repo_path in Transaction._active_transactions:
                del Transaction._active_transactions[repo_path]

            logger.info(f"Transaction {self._transaction_id} rolled back")

        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            # Try to at least get back to main
            try:
                await self._original_repo.reset_to_main()
            except Exception:
                pass
            raise TransactionError(f"Failed to rollback transaction: {e}") from e

    async def write_escalation_required(self) -> None:
        """Signal that write operations are about to occur.

        This should be called before any write operations to ensure
        the transaction is using a temporary clone.
        """
        if not self._active:
            raise TransactionStateError("No active transaction")

        await self._escalate_to_write()

    async def operation_complete(self, message: str) -> None:
        """Signal that an operation is complete and should be committed.

        This allows ai-db to create a commit after each successful operation
        as required by the specification.

        Args:
            message: Commit message for this operation
        """
        if not self._active:
            raise TransactionStateError("No active transaction")

        if self._write_escalated and self._working_repo:
            # Commit the operation
            await self._working_repo.commit_all(message)

    async def operation_failed(self, error_message: str) -> None:
        """Signal that an operation failed - create a failure branch.

        This method is called by ai-db/ai-frontend when an operation fails.
        It creates a failure branch with the current state for debugging.

        Args:
            error_message: Error message to include in the commit
        """
        if not self._active:
            raise TransactionStateError("No active transaction")

        try:
            # Create a failure branch name
            failure_branch = f"failed-transaction-{self._timestamp}-{self._transaction_id}"

            if self._write_escalated and self._working_repo:
                # Commit the current state with the error message
                await self._working_repo.commit_all(f"Failed operation: {error_message}")

                # Push the failure state back to original repo
                remote_name = f"clone_{self._transaction_id}"
                try:
                    remote = await asyncio.to_thread(
                        self._original_repo.repo.create_remote,
                        remote_name,
                        str(self._working_repo.path),
                    )

                    # Fetch the transaction branch from clone
                    await asyncio.to_thread(
                        remote.fetch, refspec=f"{self._branch_name}:{failure_branch}", force=True
                    )

                    # Remove the temporary remote
                    await asyncio.to_thread(self._original_repo.repo.delete_remote, remote)

                    logger.info(f"Created failure branch: {failure_branch}")
                except Exception as e:
                    logger.error(f"Could not create failure branch: {e}")
                    # Try to clean up remote if it exists
                    try:
                        if remote_name in [r.name for r in self._original_repo.repo.remotes]:
                            remote = self._original_repo.repo.remotes[remote_name]
                            await asyncio.to_thread(self._original_repo.repo.delete_remote, remote)
                    except Exception:
                        pass
            else:
                # No writes occurred, but still create a failure branch
                await self._original_repo.create_branch(failure_branch)
                logger.info(f"Created failure branch: {failure_branch} (no writes)")

            # The transaction should now be rolled back by the caller

        except Exception as e:
            logger.error(f"Error creating failure branch: {e}")
            # Don't raise, as we're already in a failure path
