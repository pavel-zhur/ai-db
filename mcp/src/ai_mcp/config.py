"""Configuration for MCP servers."""

from pathlib import Path
from typing import Optional

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

    # AI-DB specific settings
    max_retry_attempts: int = Field(
        default=3, gt=0, description="Maximum retry attempts for operations"
    )

    # AI API settings (passed through to ai-db library)
    ai_api_key: Optional[str] = Field(default=None, description="AI API key")
    ai_api_base: str = Field(default="https://api.openai.com/v1", description="AI API base URL")
    ai_model: str = Field(default="gpt-4", description="AI model to use")
    ai_temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="AI temperature")
    ai_timeout_seconds: int = Field(default=60, gt=0, description="AI API timeout")
    ai_max_retries: int = Field(default=3, ge=0, description="AI API max retries")


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

    # AI-Frontend specific settings
    claude_code_timeout: int = Field(
        default=600, gt=0, description="Claude Code timeout in seconds"
    )
    claude_code_docker_image: str = Field(
        default="anthropics/claude-code:latest", description="Claude Code Docker image"
    )
    max_iterations: int = Field(default=5, gt=0, description="Maximum generation iterations")
    retry_attempts: int = Field(default=2, ge=0, description="Retry attempts for operations")

    # Frontend generation settings (passed through to ai-frontend library)
    api_base_url: str = Field(
        default="http://localhost:8000", description="API base URL for generated frontend"
    )
    use_material_ui: bool = Field(default=True, description="Use Material-UI in generated frontend")
    typescript_strict: bool = Field(default=True, description="Use strict TypeScript compilation")
