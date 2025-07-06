"""Utility functions for git-layer."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

import git

logger = logging.getLogger(__name__)


def cleanup_old_transaction_branches(repo: git.Repo, keep_hours: int = 24) -> List[str]:
    """Clean up old transaction branches.
    
    Args:
        repo: GitPython repository object
        keep_hours: Number of hours to keep failed transaction branches
        
    Returns:
        List of deleted branch names
    """
    deleted = []
    current_time = datetime.now()
    
    for branch in repo.heads:
        if branch.name.startswith("transaction-") and branch.name != repo.active_branch.name:
            try:
                # Get the last commit time on this branch
                last_commit_time = datetime.fromtimestamp(branch.commit.committed_date)
                age_hours = (current_time - last_commit_time).total_seconds() / 3600
                
                if age_hours > keep_hours:
                    branch_name = branch.name
                    repo.delete_head(branch, force=True)
                    deleted.append(branch_name)
                    logger.info(f"Deleted old transaction branch: {branch_name}")
                    
            except Exception as e:
                logger.warning(f"Could not check/delete branch {branch.name}: {e}")
    
    return deleted


def ensure_git_user_config(repo: git.Repo) -> None:
    """Ensure Git user configuration is set for the repository.
    
    Args:
        repo: GitPython repository object
    """
    config = repo.config_writer()
    
    try:
        # Check if user.name and user.email are set
        if not repo.config_reader().has_option("user", "name"):
            config.set_value("user", "name", "git-layer")
            
        if not repo.config_reader().has_option("user", "email"):
            config.set_value("user", "email", "git-layer@localhost")
            
        config.release()
        
    except Exception as e:
        logger.warning(f"Could not set Git user config: {e}")
        try:
            config.release()
        except Exception:
            pass


def is_transaction_branch(branch_name: str) -> bool:
    """Check if a branch name is a transaction branch.
    
    Args:
        branch_name: Name of the branch
        
    Returns:
        True if this is a transaction branch
    """
    return branch_name.startswith("transaction-")