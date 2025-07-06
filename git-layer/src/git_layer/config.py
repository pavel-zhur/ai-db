"""Configuration for git-layer."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class GitLayerConfig(BaseSettings):
    """Configuration for git-layer."""

    model_config = SettingsConfigDict(env_prefix="GIT_LAYER_")

    # Git user configuration
    git_user_name: str = "AI-DB System"
    git_user_email: str = "ai-db@localhost"

    # Transaction settings
    transaction_branch_prefix: str = "transaction"
    failure_branch_prefix: str = "failed-transaction"
    rollback_branch_prefix: str = "transaction"

    # Cleanup settings
    cleanup_old_branches_hours: int = 24

    # Clone settings
    temp_clone_prefix: str = "git-layer-"

    # Write lock settings
    write_lock_filename: str = "ai-db-write.lock"
