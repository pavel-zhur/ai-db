"""Test configuration and fixtures."""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ["AI_HUB_GIT_REPO_PATH"] = "/tmp/test-repo"
os.environ["AI_HUB_AI_DB_API_KEY"] = "test-key"

from ai_hub.config import Config
from ai_hub.main import app
from ai_hub.service import AIHubService


@pytest.fixture
def test_config():
    """Test configuration with test paths."""
    return Config(git_repo_path="/tmp/test-repo", ai_db_api_key="test-key")


@pytest.fixture
def mock_service():
    """Mock AI-Hub service."""
    service = AsyncMock(spec=AIHubService)
    return service


@pytest.fixture
def client():
    """Test client for sync tests."""
    # Mock the service creation and configuration
    with patch("ai_hub.main._service_instance", None):
        with patch("ai_hub.main.Config") as mock_config_class:
            mock_config = Mock()
            mock_config.host = "0.0.0.0"
            mock_config.port = 8000
            mock_config.cors_origins = ["*"]
            mock_config.git_repo_path = "/tmp/test-repo"
            mock_config_class.return_value = mock_config
            return TestClient(app)


@pytest.fixture
async def async_client():
    """Test client for async tests."""
    # Mock the service creation and configuration
    with patch("ai_hub.main._service_instance", None):
        with patch("ai_hub.main.Config") as mock_config_class:
            mock_config = Mock()
            mock_config.host = "0.0.0.0"
            mock_config.port = 8000
            mock_config.cors_origins = ["*"]
            mock_config.git_repo_path = "/tmp/test-repo"
            mock_config_class.return_value = mock_config
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
