"""Configuration management for ai-frontend."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AiFrontendConfig:
    """Configuration for AI-Frontend operations."""

    # Claude Code CLI settings
    claude_code_path: str = "claude"
    claude_code_args: list[str] = field(default_factory=lambda: ["--no-interactive"])
    max_iterations: int = 5
    timeout_seconds: int = 300

    # Frontend generation settings
    use_material_ui: bool = True
    use_vite: bool = True
    typescript_strict: bool = True
    
    # API configuration
    api_base_url: str = "http://localhost:8000"
    api_retry_attempts: int = 3
    api_retry_delay: float = 1.0
    
    # Chrome MCP settings
    enable_chrome_mcp: bool = True
    chrome_mcp_port: int = 9222
    
    # Build settings
    node_version: str = "18"
    npm_registry: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_claude_output: bool = True
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert config to environment variables for subprocess."""
        env = {}
        
        if self.npm_registry:
            env["NPM_CONFIG_REGISTRY"] = self.npm_registry
            
        if self.enable_chrome_mcp:
            env["CHROME_MCP_PORT"] = str(self.chrome_mcp_port)
            
        return env