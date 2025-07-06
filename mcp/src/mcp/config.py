"""Configuration for MCP servers."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Base configuration for MCP servers."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"
    
    # Server settings
    server_name: str = "ai-db-mcp-server"
    server_version: str = "0.1.0"
    
    # Timeouts
    operation_timeout: int = 300  # 5 minutes
    
    # Development mode
    use_mocks: bool = False


class AIDBConfig(ServerConfig):
    """Configuration for AI-DB MCP server."""
    
    model_config = SettingsConfigDict(env_prefix="AI_DB_")
    
    server_name: str = "ai-db-mcp-server"
    
    # AI-DB specific settings
    ai_db_config_path: Optional[str] = None
    max_retry_attempts: int = 3
    
    # Git layer settings
    git_repo_path: str = "/workspace/data"


class AIFrontendConfig(ServerConfig):
    """Configuration for AI-Frontend MCP server."""
    
    model_config = SettingsConfigDict(env_prefix="AI_FRONTEND_")
    
    server_name: str = "ai-frontend-mcp-server"
    
    # AI-Frontend specific settings
    ai_frontend_config_path: Optional[str] = None
    claude_code_timeout: int = 600  # 10 minutes
    
    # Git layer settings
    git_repo_path: str = "/workspace/frontend"