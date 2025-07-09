"""Test configuration and fixtures."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from rich.console import Console

from console.command_parser import CommandParser
from console.config import AIDBConfig, AIFrontendConfig, Config, ConsoleConfig, GitLayerConfig
from console.logging import TraceLogger
from console.models import OutputFormat, SessionState
from console.output_formatter import OutputFormatter


@pytest.fixture
def test_config() -> Config:
    """Test configuration."""
    return Config(
        ai_db=AIDBConfig(
            api_base="http://test-api",
            api_key="test-key",
            model="test-model",
            temperature=0.1,
            max_retries=2,
            timeout_seconds=15.0,
        ),
        ai_frontend=AIFrontendConfig(
            claude_code_path="test-claude", api_base_url="http://test-api"
        ),
        git_layer=GitLayerConfig(repo_path="./test-data"),
        console=ConsoleConfig(log_file="test.log", trace_file="test_trace.log", debug_mode=False),
    )


@pytest.fixture
def console() -> Console:
    """Rich console for testing."""
    return Console(force_terminal=True, width=120)


@pytest.fixture
def trace_logger(tmp_path: Path) -> TraceLogger:
    """Trace logger for testing."""
    return TraceLogger(tmp_path / "trace.log")


@pytest.fixture
def command_parser() -> CommandParser:
    """Command parser instance."""
    return CommandParser()


@pytest.fixture
def output_formatter(console: Console) -> OutputFormatter:
    """Output formatter instance."""
    return OutputFormatter(console, max_width=120)


@pytest.fixture
def session_state() -> SessionState:
    """Session state instance."""
    return SessionState(conversation_history=[], current_output_format=OutputFormat.TABLE)


@pytest.fixture
def mock_ai_db() -> AsyncMock:
    """Mock AI-DB instance."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_ai_frontend() -> AsyncMock:
    """Mock AI-Frontend instance."""
    mock = AsyncMock()
    mock.generate_frontend = AsyncMock()
    return mock


@pytest.fixture
def mock_git_transaction() -> AsyncMock:
    """Mock Git transaction."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.begin = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.path = "/test/repo"
    mock.id = "test-transaction-id"
    return mock
