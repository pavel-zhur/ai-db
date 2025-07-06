"""Transaction management for git-layer."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from uuid import uuid4

from .repository import GitRepository
from .exceptions import TransactionError, TransactionStateError

logger = logging.getLogger(__name__)


class Transaction:
    """Manages a Git-based transaction with BEGIN/COMMIT/ROLLBACK semantics."""
    
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
    def path(self) -> str:
        """Get the current working directory path.
        
        Returns:
            Path to the repository (original or clone)
        """
        if self._working_repo:
            return str(self._working_repo.path)
        return str(self._original_repo.path)
    
    @property
    def transaction_id(self) -> str:
        """Get the transaction ID."""
        return self._transaction_id
    
    @property
    def is_active(self) -> bool:
        """Check if the transaction is active."""
        return self._active
    
    def __enter__(self) -> "Transaction":
        """Begin the transaction."""
        self.begin()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End the transaction, committing on success or rolling back on failure."""
        if exc_type is None:
            try:
                self.commit()
            except Exception:
                logger.exception("Failed to commit transaction")
                self.rollback()
                raise
        else:
            logger.info(f"Transaction failed with {exc_type.__name__}: {exc_val}")
            self.rollback()
    
    def __del__(self) -> None:
        """Cleanup transaction if it wasn't properly closed."""
        if self._active:
            logger.warning(f"Transaction {self._transaction_id} was not properly closed, rolling back")
            try:
                self.rollback()
            except Exception:
                logger.exception("Failed to rollback abandoned transaction")
    
    def begin(self) -> None:
        """Begin a new transaction by creating a branch."""
        if self._active:
            raise TransactionStateError("Transaction already active")
        
        try:
            # Ensure main branch is clean
            self._original_repo.ensure_clean_working_tree()
            
            # Create transaction branch
            self._original_repo.create_branch(self._branch_name)
            
            self._active = True
            logger.info(f"Transaction {self._transaction_id} started")
            
        except Exception as e:
            raise TransactionError(f"Failed to begin transaction: {e}") from e
    
    def _escalate_to_write(self) -> None:
        """Escalate to write mode by creating a temporary clone."""
        if self._write_escalated:
            return
            
        try:
            logger.info(f"Escalating transaction {self._transaction_id} to write mode")
            
            # Create a temporary clone
            self._working_repo = self._original_repo.clone_to_temp()
            
            # Checkout the transaction branch in the clone
            self._working_repo.checkout_branch(self._branch_name)
            
            self._write_escalated = True
            
        except Exception as e:
            raise TransactionError(f"Failed to escalate to write mode: {e}") from e
    
    def _detect_write_operation(self) -> None:
        """Check if any files have been modified and escalate if needed."""
        if not self._active:
            return
            
        # For now, we'll rely on the client to trigger write escalation
        # by accessing the path property after making changes
        # In a more sophisticated implementation, we could monitor file changes
        pass
    
    def checkpoint(self, message: Optional[str] = None) -> None:
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
                self._working_repo.commit_all(commit_message)
        except Exception as e:
            raise TransactionError(f"Failed to create checkpoint: {e}") from e
    
    def commit(self) -> None:
        """Commit the transaction by merging to main."""
        if not self._active:
            raise TransactionStateError("No active transaction")
        
        if self._committed:
            raise TransactionStateError("Transaction already committed")
        
        try:
            if self._write_escalated:
                # Commit any pending changes
                self.checkpoint("Final checkpoint before merge")
                
                # Push changes back to original repo
                # We need to fetch from the clone to the original
                # Add the working repo as a remote to the original
                remote_name = f"clone_{self._transaction_id}"
                try:
                    # Add remote to original repo pointing to clone
                    self._original_repo.repo.create_remote(remote_name, str(self._working_repo.path))
                    
                    # Fetch the transaction branch from clone
                    self._original_repo.repo.remotes[remote_name].fetch(
                        refspec=f"{self._branch_name}:{self._branch_name}",
                        force=True
                    )
                    
                    # Remove the temporary remote
                    self._original_repo.repo.delete_remote(remote_name)
                except Exception:
                    # Try to clean up remote if it exists
                    try:
                        self._original_repo.repo.delete_remote(remote_name)
                    except Exception:
                        pass
                    raise
                
                # Merge to main in the original repo
                merge_message = f"Transaction {self._transaction_id}: {self._message}"
                self._original_repo.merge_branch(self._branch_name, merge_message)
                
                # Cleanup the clone
                self._working_repo.cleanup_clone()
                self._working_repo = None
            else:
                # No writes occurred, just merge the empty branch to main
                # Actually, no need to merge if no changes were made
                logger.info("No changes in transaction, skipping merge")
            
            # Delete the transaction branch
            self._original_repo.delete_branch(self._branch_name)
            
            self._committed = True
            self._active = False
            
            logger.info(f"Transaction {self._transaction_id} committed")
            
        except Exception as e:
            raise TransactionError(f"Failed to commit transaction: {e}") from e
    
    def rollback(self) -> None:
        """Rollback the transaction by abandoning the branch."""
        if not self._active:
            return  # Already rolled back or not started
        
        try:
            if self._write_escalated and self._working_repo:
                # Commit current state to the branch for debugging
                try:
                    self.checkpoint("Rollback checkpoint")
                    
                    # Push the rollback state back to original repo
                    remote_name = f"clone_{self._transaction_id}"
                    try:
                        self._original_repo.repo.create_remote(remote_name, str(self._working_repo.path))
                        self._original_repo.repo.remotes[remote_name].fetch(
                            refspec=f"{self._branch_name}:{self._branch_name}",
                            force=True
                        )
                        self._original_repo.repo.delete_remote(remote_name)
                    except Exception:
                        logger.warning("Could not push rollback state to original repo")
                except Exception:
                    logger.warning("Could not create rollback checkpoint")
                
                # Cleanup the clone
                if self._working_repo:
                    self._working_repo.cleanup_clone()
                    self._working_repo = None
            
            # Return to main branch in original repo
            self._original_repo.reset_to_main()
            
            # Note: We keep the transaction branch for debugging
            # In production, you might want to delete it after some time
            
            self._active = False
            
            logger.info(f"Transaction {self._transaction_id} rolled back")
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            # Try to at least get back to main
            try:
                self._original_repo.reset_to_main()
            except Exception:
                pass
            raise TransactionError(f"Failed to rollback transaction: {e}") from e
    
    def write_escalation_required(self) -> None:
        """Signal that write operations are about to occur.
        
        This should be called before any write operations to ensure
        the transaction is using a temporary clone.
        """
        if not self._active:
            raise TransactionStateError("No active transaction")
        
        self._escalate_to_write()
    
    def operation_complete(self, message: str) -> None:
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
            self._working_repo.commit_all(message)