"""Test configuration and fixtures."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from rich.console import Console

from console.config import Config, ConsoleConfig, AIDBConfig, AIFrontendConfig, GitLayerConfig
from console.logging import TraceLogger
from console.command_parser import CommandParser
from console.output_formatter import OutputFormatter
from console.models import SessionState, OutputFormat


@pytest.fixture
def test_config():
    """Test configuration."""
    return Config(
        ai_db=AIDBConfig(
            api_base="http://test-api",
            api_key="test-key",
            model="test-model"
        ),
        ai_frontend=AIFrontendConfig(
            claude_code_path="test-claude"
        ),
        git_layer=GitLayerConfig(
            repo_path="./test-data"
        ),
        console=ConsoleConfig(
            log_file="test.log",
            trace_file="test_trace.log",
            debug_mode=False
        )
    )


@pytest.fixture
def console():
    """Rich console for testing."""
    return Console(force_terminal=True, width=120)


@pytest.fixture
def trace_logger(tmp_path):
    """Trace logger for testing."""
    return TraceLogger(tmp_path / "trace.log")


@pytest.fixture
def command_parser():
    """Command parser instance."""
    return CommandParser()


@pytest.fixture
def output_formatter(console):
    """Output formatter instance."""
    return OutputFormatter(console, max_width=120)


@pytest.fixture
def session_state():
    """Session state instance."""
    return SessionState(
        conversation_history=[],
        current_output_format=OutputFormat.TABLE
    )


@pytest.fixture
def mock_ai_db():
    """Mock AI-DB instance."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_ai_frontend():
    """Mock AI-Frontend instance."""
    mock = AsyncMock()
    mock.generate_frontend = AsyncMock()
    return mock


@pytest.fixture
def mock_git_transaction():
    """Mock Git transaction."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.path = "/test/repo"
    return mock