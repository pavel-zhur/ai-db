"""Test configuration management."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from console.config import Config, load_config


def test_default_config() -> None:
    """Test loading default configuration."""
    config = load_config()

    assert config.ai_db.api_base == "https://api.openai.com/v1"
    assert config.ai_db.model == "gpt-4"
    assert config.ai_db.temperature == 0.0
    assert config.ai_db.max_retries == 3

    assert config.ai_frontend.claude_code_path == "claude"
    assert config.ai_frontend.max_iterations == 5

    assert config.git_layer.repo_path == "./data"

    assert config.console.log_file == "console.log"
    assert config.console.trace_file == "console_trace.log"
    assert config.console.debug_mode is False
    assert config.console.default_output_format == "table"


def test_load_from_file() -> None:
    """Test loading configuration from file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "ai_db": {
                "api_base": "http://custom-api",
                "api_key": "custom-key",
                "model": "custom-model",
            },
            "console": {"debug_mode": True, "default_output_format": "json"},
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        assert config.ai_db.api_base == "http://custom-api"
        assert config.ai_db.api_key == "custom-key"
        assert config.ai_db.model == "custom-model"
        assert config.console.debug_mode is True
        assert config.console.default_output_format == "json"
    finally:
        os.unlink(config_path)


def test_environment_override() -> None:
    """Test environment variable overrides."""
    env_vars = {
        "AI_DB_API_BASE": "http://env-api",
        "AI_DB_API_KEY": "env-key",
        "AI_DB_MODEL": "env-model",
        "AI_DB_MAX_RETRIES": "5",
        "CONSOLE_DEBUG": "true",
        "CONSOLE_LOG_FILE": "env.log",
    }

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    try:
        config = load_config()

        assert config.ai_db.api_base == "http://env-api"
        assert config.ai_db.api_key == "env-key"
        assert config.ai_db.model == "env-model"
        assert config.ai_db.max_retries == 5
        assert config.console.debug_mode is True
        assert config.console.log_file == "env.log"
    finally:
        # Clean up environment
        for key in env_vars:
            os.environ.pop(key, None)


def test_config_validation() -> None:
    """Test configuration validation."""
    from console.config import AIDBConfig, ConsoleConfig

    # Test invalid output format
    with pytest.raises(ValueError):
        Config(console=ConsoleConfig(default_output_format="invalid"))

    # Test valid configurations
    config = Config(ai_db=AIDBConfig(max_retries=5), console=ConsoleConfig(page_size=100))
    assert config.ai_db.max_retries == 5
    assert config.console.page_size == 100
