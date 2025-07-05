"""Pytest configuration and fixtures."""

import pytest
from typing import Any
import structlog

from src.mocks import MockAIDB, MockAIFrontend, MockGitLayer
from src.config import AIDBConfig, AIFrontendConfig


@pytest.fixture
def mock_logger() -> structlog.BoundLogger:
    """Create a test logger."""
    return structlog.get_logger()


@pytest.fixture
def mock_ai_db() -> MockAIDB:
    """Create a mock AI-DB instance."""
    return MockAIDB()


@pytest.fixture
def mock_ai_frontend() -> MockAIFrontend:
    """Create a mock AI-Frontend instance."""
    return MockAIFrontend()


@pytest.fixture
def mock_git_layer() -> MockGitLayer:
    """Create a mock Git-Layer instance."""
    return MockGitLayer("/tmp/test-repo")


@pytest.fixture
def ai_db_config() -> AIDBConfig:
    """Create AI-DB config for testing."""
    return AIDBConfig(
        use_mocks=True,
        log_level="DEBUG",
        log_format="console",
    )


@pytest.fixture
def ai_frontend_config() -> AIFrontendConfig:
    """Create AI-Frontend config for testing."""
    return AIFrontendConfig(
        use_mocks=True,
        log_level="DEBUG",
        log_format="console",
    )