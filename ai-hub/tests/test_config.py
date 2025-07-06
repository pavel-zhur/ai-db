"""Tests for AI-Hub configuration."""

import os
from unittest.mock import patch

from ai_hub.config import Config


class TestConfig:
    """Test Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        # Server settings
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.cors_origins == ["*"]

        # Git repository settings
        assert config.git_repo_path == "/data/repos"

        # AI-DB settings
        assert config.ai_db_api_base == "https://api.openai.com/v1"
        assert config.ai_db_api_key == ""
        assert config.ai_db_model == "gpt-4"
        assert config.ai_db_temperature == 0.1
        assert config.ai_db_max_retries == 3
        assert config.ai_db_timeout_seconds == 60

        # Git-layer settings
        assert config.git_user_name == "AI-Hub System"
        assert config.git_user_email == "ai-hub@localhost"
        assert config.git_transaction_branch_prefix == "ai-hub-transaction"
        assert config.git_write_lock_filename == "ai-hub-write.lock"

        # Progress feedback settings
        assert config.progress_feedback_interval == 30

    def test_env_prefix(self):
        """Test environment variable prefix."""
        with patch.dict(os.environ, {
            "AI_HUB_HOST": "127.0.0.1",
            "AI_HUB_PORT": "9000",
            "AI_HUB_GIT_REPO_PATH": "/custom/path",
            "AI_HUB_AI_DB_API_KEY": "test-key",
            "AI_HUB_AI_DB_MODEL": "gpt-3.5-turbo",
        }):
            config = Config()
            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert config.git_repo_path == "/custom/path"
            assert config.ai_db_api_key == "test-key"
            assert config.ai_db_model == "gpt-3.5-turbo"

    def test_cors_origins_list(self):
        """Test CORS origins as list."""
        with patch.dict(os.environ, {
            "AI_HUB_CORS_ORIGINS": '["http://localhost:3000", "https://example.com"]'
        }):
            config = Config()
            assert config.cors_origins == ["http://localhost:3000", "https://example.com"]

    def test_boolean_settings(self):
        """Test boolean configuration settings."""
        with patch.dict(os.environ, {
            "AI_HUB_AI_DB_TEMPERATURE": "0.5",
        }):
            config = Config()
            assert config.ai_db_temperature == 0.5

    def test_numeric_settings(self):
        """Test numeric configuration settings."""
        with patch.dict(os.environ, {
            "AI_HUB_PORT": "8080",
            "AI_HUB_AI_DB_TEMPERATURE": "0.5",
            "AI_HUB_AI_DB_MAX_RETRIES": "5",
            "AI_HUB_AI_DB_TIMEOUT_SECONDS": "60",
            "AI_HUB_PROGRESS_FEEDBACK_INTERVAL": "15",
        }):
            config = Config()
            assert config.port == 8080
            assert config.ai_db_temperature == 0.5
            assert config.ai_db_max_retries == 5
            assert config.ai_db_timeout_seconds == 60
            assert config.progress_feedback_interval == 15
