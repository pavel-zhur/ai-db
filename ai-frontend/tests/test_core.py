"""Tests for ai-frontend core functionality."""

from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest

from ai_frontend.config import AiFrontendConfig
from ai_frontend.core import AiFrontend


class MockTransaction:
    """Mock transaction for testing."""

    def __init__(self, path: Path):
        self._path = path
        self._id = "test-transaction-123"
        self.write_escalation_called = False
        self.operation_complete_called = False
        self.operation_failed_called = False
        self.complete_message: Optional[str] = None
        self.failed_message: Optional[str] = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def path(self) -> Path:
        return self._path

    async def write_escalation_required(self) -> None:
        self.write_escalation_called = True

    async def operation_complete(self, message: str) -> None:
        self.operation_complete_called = True
        self.complete_message = message

    async def operation_failed(self, error_message: str) -> None:
        self.operation_failed_called = True
        self.failed_message = error_message


@pytest.fixture
def config():
    """Create test configuration."""
    return AiFrontendConfig(
        log_level="DEBUG",
        max_iterations=2,
        retry_attempts=1,
    )


@pytest.fixture
def ai_frontend(config):
    """Create AiFrontend instance."""
    return AiFrontend(config)


@pytest.fixture
def mock_transaction(tmp_path):
    """Create mock transaction."""
    return MockTransaction(tmp_path)


@pytest.fixture
def sample_schema():
    """Create sample schema for testing."""
    return {
        "tables": {
            "users": {
                "columns": {
                    "id": {
                        "type": "integer",
                        "primary_key": True,
                        "auto_increment": True,
                    },
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "required": True,
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                    },
                }
            }
        }
    }


@pytest.mark.asyncio
async def test_generate_frontend_success(ai_frontend, mock_transaction, sample_schema, tmp_path):
    """Test successful frontend generation."""
    # Create frontend directory
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    # Mock the internal components
    with (
        patch.object(ai_frontend._skeleton_generator, "generate", AsyncMock()) as mock_skeleton,
        patch.object(ai_frontend._api_generator, "generate_api_layer", AsyncMock()) as mock_api,
        patch.object(
            ai_frontend._claude_wrapper, "generate_frontend", AsyncMock(return_value=True)
        ) as mock_claude,
        patch.object(
            ai_frontend._compiler, "compile_and_validate", AsyncMock(return_value=(True, None))
        ) as mock_compile,
    ):

        result = await ai_frontend.generate_frontend(
            request="Create a user management interface",
            schema=sample_schema,
            transaction=mock_transaction,
        )

        assert result.success is True
        assert result.error is None
        assert result.compiled is True
        assert mock_transaction.write_escalation_called is True
        assert mock_transaction.operation_complete_called is True
        assert "Generate frontend:" in mock_transaction.complete_message

        # Verify all components were called
        mock_skeleton.assert_called_once()
        mock_api.assert_called_once()
        mock_claude.assert_called_once()
        mock_compile.assert_called()


@pytest.mark.asyncio
async def test_generate_frontend_compilation_failure(ai_frontend, mock_transaction, sample_schema):
    """Test frontend generation with compilation failure."""
    with (
        patch.object(ai_frontend._skeleton_generator, "generate", AsyncMock()),
        patch.object(ai_frontend._api_generator, "generate_api_layer", AsyncMock()),
        patch.object(
            ai_frontend._claude_wrapper, "generate_frontend", AsyncMock(return_value=True)
        ),
        patch.object(
            ai_frontend._compiler,
            "compile_and_validate",
            AsyncMock(return_value=(False, "TypeScript error")),
        ),
    ):

        result = await ai_frontend.generate_frontend(
            request="Create a user interface",
            schema=sample_schema,
            transaction=mock_transaction,
        )

        assert result.success is False
        assert result.error == "TypeScript error"
        assert result.compiled is False
        assert mock_transaction.operation_failed_called is True
        assert "Frontend compilation failed:" in mock_transaction.failed_message


@pytest.mark.asyncio
async def test_generate_frontend_with_retry(ai_frontend, mock_transaction, sample_schema):
    """Test frontend generation with retry logic."""
    # First call fails, second succeeds
    mock_claude = AsyncMock(
        side_effect=[
            Exception("Network error"),
            True,
        ]
    )

    with (
        patch.object(ai_frontend._skeleton_generator, "generate", AsyncMock()),
        patch.object(ai_frontend._api_generator, "generate_api_layer", AsyncMock()),
        patch.object(ai_frontend._claude_wrapper, "generate_frontend", mock_claude),
        patch.object(
            ai_frontend._compiler, "compile_and_validate", AsyncMock(return_value=(True, None))
        ),
    ):

        result = await ai_frontend.generate_frontend(
            request="Create a user interface",
            schema=sample_schema,
            transaction=mock_transaction,
        )

        assert result.success is True
        assert mock_claude.call_count == 2  # Initial + 1 retry


@pytest.mark.asyncio
async def test_update_frontend_no_existing(ai_frontend, mock_transaction, sample_schema, tmp_path):
    """Test updating frontend when no frontend exists."""
    result = await ai_frontend.update_frontend(
        request="Add search functionality",
        schema=sample_schema,
        transaction=mock_transaction,
    )

    assert result.success is False
    assert result.error == "No existing frontend found to update"
    assert not mock_transaction.operation_complete_called
    assert not mock_transaction.operation_failed_called


@pytest.mark.asyncio
async def test_get_schema_exists(ai_frontend, mock_transaction, tmp_path):
    """Test getting existing schema."""
    # Create schema file
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    schema_file = frontend_dir / "schema.yaml"
    schema_file.write_text(
        """
tables:
  users:
    columns:
      id:
        type: integer
"""
    )

    schema = await ai_frontend.get_schema(mock_transaction)

    assert schema is not None
    assert "tables" in schema
    assert "users" in schema["tables"]


@pytest.mark.asyncio
async def test_get_schema_not_exists(ai_frontend, mock_transaction):
    """Test getting schema when none exists."""
    schema = await ai_frontend.get_schema(mock_transaction)
    assert schema is None


@pytest.mark.asyncio
async def test_init_from_folder_success(ai_frontend, mock_transaction, tmp_path):
    """Test initializing from a seed folder."""
    # Create source folder with files
    source_dir = tmp_path / "seed"
    source_dir.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (source_dir / "package.json").write_text('{"name": "test"}')
    (source_dir / "src").mkdir()
    (source_dir / "src/App.tsx").write_text("export default function App() {}")

    # Mock the compiler
    with patch.object(
        ai_frontend._compiler, "compile_and_validate", AsyncMock(return_value=(True, None))
    ):
        await ai_frontend.init_from_folder(source_dir, mock_transaction)

        assert mock_transaction.write_escalation_called is True
        assert mock_transaction.operation_complete_called is True
        assert "Initialize frontend from seed" in mock_transaction.complete_message

        # Check files were copied
        target_dir = mock_transaction.path / "frontend"
        assert (target_dir / "package.json").exists()
        assert (target_dir / "src/App.tsx").exists()


@pytest.mark.asyncio
async def test_init_from_folder_validation_failure(ai_frontend, mock_transaction, tmp_path):
    """Test initializing from folder with validation failure."""
    source_dir = tmp_path / "seed"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "package.json").write_text('{"name": "test"}')

    # Mock the compiler to fail
    with patch.object(
        ai_frontend._compiler,
        "compile_and_validate",
        AsyncMock(return_value=(False, "Invalid TypeScript")),
    ):
        with pytest.raises(Exception) as exc_info:
            await ai_frontend.init_from_folder(source_dir, mock_transaction)

        assert "Frontend validation failed" in str(exc_info.value)
        assert mock_transaction.operation_failed_called is True
