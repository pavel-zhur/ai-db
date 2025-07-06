"""Configuration for AI-Hub."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """AI-Hub configuration."""

    # Server settings
    host: str = "0.0.0.0"  # Default is reasonable for server binding
    port: int = 8000  # Standard default port
    cors_origins: list[str] = ["*"]  # Default for development

    # Git repository settings
    git_repo_path: str = "/data/repos"  # Standard path in container

    # AI-DB settings - these map to AI_DB_* environment variables
    # AI-Hub will set these in the environment for AI-DB to pick up
    ai_db_api_key: str = ""  # Empty default for development/testing
    ai_db_api_base: str = "https://api.openai.com/v1"  # Standard OpenAI endpoint
    ai_db_model: str = "gpt-4"  # Reasonable default model
    ai_db_temperature: float = 0.1  # Low temperature for consistency
    ai_db_timeout_seconds: int = 60  # Reasonable timeout
    ai_db_max_retries: int = 3  # Standard retry count

    # Git-layer settings (passed through to git-layer)
    git_user_name: str = "AI-Hub System"
    git_user_email: str = "ai-hub@localhost"
    git_transaction_branch_prefix: str = "ai-hub-transaction"
    git_write_lock_filename: str = "ai-hub-write.lock"

    # Progress feedback settings
    progress_feedback_interval: int = 30  # 30 seconds is reasonable

    model_config = {"env_prefix": "AI_HUB_"}
