"""Configuration management for ai-frontend."""

from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AiFrontendConfig(BaseSettings):
    """Configuration for AI-Frontend operations using pydantic BaseSettings."""

    model_config = SettingsConfigDict(
        env_prefix="AI_FRONTEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Claude Code CLI settings
    claude_code_path: str = Field(default="claude", description="Path to Claude Code CLI")
    claude_code_docker_image: str = Field(
        default="anthropics/claude-code:latest",
        description="Docker image for Claude Code",
    )
    max_iterations: int = Field(default=5, description="Max iterations for Claude Code")
    timeout_seconds: int = Field(default=300, description="Timeout for Claude Code operations")
    retry_attempts: int = Field(default=2, description="Number of retry attempts for operations")

    # Frontend generation settings
    use_material_ui: bool = Field(default=True, description="Use Material-UI components")
    use_vite: bool = Field(default=True, description="Use Vite as build tool")
    typescript_strict: bool = Field(default=True, description="Enable TypeScript strict mode")

    # API configuration
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for AI-DB API",
    )
    api_retry_attempts: int = Field(default=3, description="API call retry attempts")
    api_retry_delay: float = Field(default=1.0, description="Delay between API retries")

    # Chrome MCP settings
    enable_chrome_mcp: bool = Field(default=True, description="Enable Chrome MCP for UI viewing")
    chrome_mcp_port: int = Field(default=9222, description="Port for Chrome MCP")

    # Build settings
    node_version: str = Field(default="18", description="Node.js version")
    npm_registry: Optional[str] = Field(default=None, description="Custom NPM registry")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_claude_output: bool = Field(default=True, description="Log Claude Code output")

    # Progress feedback
    progress_interval_seconds: int = Field(
        default=30,
        description="Interval for progress feedback messages",
    )

    def to_env_vars(self) -> Dict[str, str]:
        """Convert config to environment variables for subprocess."""
        env = {}

        if self.npm_registry:
            env["NPM_CONFIG_REGISTRY"] = self.npm_registry

        if self.enable_chrome_mcp:
            env["CHROME_MCP_PORT"] = str(self.chrome_mcp_port)

        return env
