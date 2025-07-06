"""Configuration for MCP servers."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """Base configuration for MCP servers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or console")

    # Server settings
    server_name: str = Field(default="mcp-server", description="Server name")
    server_version: str = Field(default="0.1.0", description="Server version")

    # Repository path where data is stored
    repo_path: Path = Field(default=Path("/workspace/data"), description="Git repository path")

    # Timeouts
    operation_timeout: int = Field(default=300, gt=0, description="Operation timeout in seconds")

    # Development mode
    use_mocks: bool = Field(default=False, description="Use mock implementations")


class AIDBMCPConfig(MCPServerConfig):
    """Configuration for AI-DB MCP server."""

    model_config = SettingsConfigDict(
        env_prefix="AI_DB_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    server_name: str = Field(default="ai-db-mcp-server", description="AI-DB MCP server name")

    # MCP-specific settings only (ai-db reads its own AI_DB_* environment variables)
    max_retry_attempts: int = Field(
        default=3, gt=0, description="Maximum retry attempts for MCP operations"
    )


class AIFrontendMCPConfig(MCPServerConfig):
    """Configuration for AI-Frontend MCP server."""

    model_config = SettingsConfigDict(
        env_prefix="AI_FRONTEND_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    server_name: str = Field(
        default="ai-frontend-mcp-server", description="AI-Frontend MCP server name"
    )

    # MCP-specific settings only (ai-frontend reads its own AI_FRONTEND_* environment variables)
    max_retry_attempts: int = Field(
        default=3, gt=0, description="Maximum retry attempts for MCP operations"
    )
