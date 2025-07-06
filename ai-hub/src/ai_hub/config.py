"""Configuration for AI-Hub."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """AI-Hub configuration."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]

    # Git repository settings
    git_repo_path: str = "/data/repos"

    # AI-DB settings - these map to AI_DB_* environment variables
    # AI-Hub will set these in the environment for AI-DB to pick up
    ai_db_api_key: str = ""
    ai_db_api_base: str = "https://api.openai.com/v1"
    ai_db_model: str = "gpt-4"
    ai_db_temperature: float = 0.1
    ai_db_timeout_seconds: int = 60
    ai_db_max_retries: int = 3

    # Git-layer settings (passed through to git-layer)
    git_user_name: str = "AI-Hub System"
    git_user_email: str = "ai-hub@localhost"
    git_transaction_branch_prefix: str = "ai-hub-transaction"
    git_write_lock_filename: str = "ai-hub-write.lock"

    # Progress feedback settings
    progress_feedback_interval: int = 30

    class Config:
        env_prefix = "AI_HUB_"
