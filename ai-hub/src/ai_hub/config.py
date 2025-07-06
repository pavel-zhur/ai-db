"""Configuration for AI-Hub."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """AI-Hub configuration."""
    
    # API settings
    api_key: str = ""
    cors_origins: list[str] = ["*"]
    
    # Git repository path
    git_repo_path: str = "/data/repos"
    
    class Config:
        env_prefix = "AI_HUB_"