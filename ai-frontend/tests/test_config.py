"""Tests for ai-frontend configuration."""

import os
from unittest.mock import patch

from ai_frontend.config import AiFrontendConfig


def test_default_config():
    """Test default configuration values."""
    config = AiFrontendConfig()

    assert config.claude_code_path == "claude"
    assert config.claude_code_docker_image == "anthropics/claude-code:latest"
    assert config.max_iterations == 5
    assert config.timeout_seconds == 300
    assert config.retry_attempts == 2
    assert config.use_material_ui is True
    assert config.use_vite is True
    assert config.typescript_strict is True
    assert config.api_base_url == "http://localhost:8000"
    assert config.log_level == "INFO"
    assert config.progress_interval_seconds == 30


def test_env_override():
    """Test environment variable overrides."""
    with patch.dict(
        os.environ,
        {
            "AI_FRONTEND_CLAUDE_CODE_PATH": "/usr/bin/claude",
            "AI_FRONTEND_MAX_ITERATIONS": "10",
            "AI_FRONTEND_API_BASE_URL": "https://api.example.com",
            "AI_FRONTEND_LOG_LEVEL": "DEBUG",
        },
    ):
        config = AiFrontendConfig()

        assert config.claude_code_path == "/usr/bin/claude"
        assert config.max_iterations == 10
        assert config.api_base_url == "https://api.example.com"
        assert config.log_level == "DEBUG"


def test_to_env_vars():
    """Test conversion to environment variables."""
    config = AiFrontendConfig(
        npm_registry="https://registry.example.com",
        enable_chrome_mcp=True,
        chrome_mcp_port=9999,
    )

    env_vars = config.to_env_vars()

    assert env_vars["NPM_CONFIG_REGISTRY"] == "https://registry.example.com"
    assert env_vars["CHROME_MCP_PORT"] == "9999"


def test_env_file_loading(tmp_path):
    """Test loading from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
AI_FRONTEND_TIMEOUT_SECONDS=600
AI_FRONTEND_RETRY_ATTEMPTS=5
AI_FRONTEND_USE_MATERIAL_UI=false
"""
    )

    config = AiFrontendConfig(_env_file=str(env_file))

    assert config.timeout_seconds == 600
    assert config.retry_attempts == 5
    assert config.use_material_ui is False
