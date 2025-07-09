"""Tests for AI-Hub service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_hub.config import Config
from ai_hub.models import PermissionLevel
from ai_hub.service import AIHubService


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Config()
    config.git_repo_path = "/test/repo"
    config.progress_feedback_interval = 1  # Short interval for testing
    return config


@pytest.fixture
def service(mock_config):
    """Create AIHubService instance with mock config."""
    with patch("ai_hub.service.os.environ"):
        with patch("ai_hub.service.AIDB") as mock_aidb:
            mock_aidb.return_value = MagicMock()
            return AIHubService(mock_config)


class TestAIHubService:
    """Test AIHubService class."""

    def test_init(self, mock_config):
        """Test service initialization."""
        with patch("ai_hub.service.os.environ") as mock_environ:
            with patch("ai_hub.service.AIDB") as mock_aidb:
                mock_aidb_instance = MagicMock()
                mock_aidb.return_value = mock_aidb_instance

                service = AIHubService(mock_config)

                # Check that environment variables were set
                assert any(
                    "AI_DB_" in str(call) for call in mock_environ.__setitem__.call_args_list
                )

                # Check that AIDB was created
                assert service._aidb == mock_aidb_instance

    def test_aidb_property(self, service):
        """Test AIDB property returns the initialized instance."""
        # AIDB is already initialized in the service fixture
        assert service.aidb is not None
        assert service.aidb == service._aidb

    def test_convert_permission_level(self, service):
        """Test permission level conversion."""
        from ai_db.core.models import PermissionLevel as AIDBPermissionLevel

        result = service._convert_permission_level(PermissionLevel.SELECT)
        assert result == AIDBPermissionLevel.SELECT

        result = service._convert_permission_level(PermissionLevel.DATA_MODIFY)
        assert result == AIDBPermissionLevel.DATA_MODIFY

    def test_convert_data_loss_indicator(self, service):
        """Test data loss indicator conversion."""
        from ai_hub.models import DataLossIndicator

        # Test with object that has value attribute
        mock_indicator = MagicMock()
        mock_indicator.value = "probable"
        result = service._convert_data_loss_indicator(mock_indicator)
        assert result == DataLossIndicator.PROBABLE

        # Test with object that doesn't have value attribute
        result = service._convert_data_loss_indicator("some_string")
        assert result == DataLossIndicator.NONE

    @pytest.mark.asyncio
    async def test_progress_feedback(self, service):
        """Test progress feedback functionality."""
        feedback_calls = []

        def mock_log_info(message):
            feedback_calls.append(message)

        with patch("ai_hub.service.logger.info", side_effect=mock_log_info):
            # Start progress feedback
            task = asyncio.create_task(service._progress_feedback("test operation"))

            # Let it run for a short time
            await asyncio.sleep(1.5)  # Should trigger at least one feedback

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Check that feedback was logged
            assert len(feedback_calls) >= 1
            assert "Still working on: test operation..." in feedback_calls[0]

    @pytest.mark.asyncio
    async def test_execute_with_progress(self, service):
        """Test operation execution with progress feedback."""

        async def mock_operation():
            await asyncio.sleep(0.1)
            return "success"

        # Create a real async task that can be cancelled
        async def mock_progress_feedback(desc):
            await asyncio.sleep(10)  # Will be cancelled before completion

        with patch.object(service, "_progress_feedback", side_effect=mock_progress_feedback):
            result = await service._execute_with_progress(mock_operation(), "test operation")
            assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_query_success(self, service):
        """Test successful query execution."""
        mock_transaction = AsyncMock()
        mock_result = MagicMock()
        mock_result.status = True
        mock_result.data = [{"id": 1, "name": "test"}]
        mock_result.schema = {"users": {"id": "int"}}  # AI-DB uses 'schema'
        mock_result.data_loss_indicator = MagicMock()
        mock_result.data_loss_indicator.value = "none"
        mock_result.ai_comment = "Query executed successfully"
        mock_result.compiled_plan = "SELECT * FROM users"
        mock_result.transaction_id = "tx123"
        mock_result.error = None
        mock_result.execution_time = 0.5

        with (
            patch("ai_hub.service.git_layer.begin") as mock_begin,
            patch.object(service, "_execute_with_progress") as mock_execute_progress,
        ):

            mock_begin.return_value.__aenter__.return_value = mock_transaction
            # Mock the execute method on the existing AIDB instance
            service._aidb.execute = AsyncMock(return_value=mock_result)

            # Mock _execute_with_progress to execute the coroutine directly
            async def execute_directly(coro, desc):
                return await coro

            mock_execute_progress.side_effect = execute_directly

            result = await service.execute_query("SELECT * FROM users", PermissionLevel.SELECT)

            assert result.success is True
            assert result.data == [{"id": 1, "name": "test"}]
            assert result.result_schema == {"users": {"id": "int"}}

            mock_transaction.operation_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, service):
        """Test query execution failure."""
        mock_transaction = AsyncMock()

        with (
            patch("ai_hub.service.git_layer.begin") as mock_begin,
            patch.object(service, "_execute_with_progress") as mock_execute_progress,
        ):

            mock_begin.return_value.__aenter__.return_value = mock_transaction
            # Mock the execute method to raise an exception
            service._aidb.execute = AsyncMock(side_effect=Exception("Query failed"))

            # Mock _execute_with_progress to execute the coroutine directly
            async def execute_directly(coro, desc):
                return await coro

            mock_execute_progress.side_effect = execute_directly

            with pytest.raises(Exception, match="Query failed"):
                await service.execute_query("INVALID QUERY", PermissionLevel.SELECT)

            mock_transaction.operation_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_view(self, service):
        """Test view execution."""
        mock_transaction = AsyncMock()
        mock_result = MagicMock()
        mock_result.status = True
        mock_result.data = [{"summary": "data"}]
        mock_result.schema = None
        mock_result.data_loss_indicator = MagicMock()
        mock_result.data_loss_indicator.value = "none"
        mock_result.ai_comment = None
        mock_result.compiled_plan = None
        mock_result.transaction_id = None
        mock_result.error = None
        mock_result.execution_time = None

        with (
            patch("ai_hub.service.git_layer.begin") as mock_begin,
            patch.object(service, "_execute_with_progress") as mock_execute_progress,
        ):

            mock_begin.return_value.__aenter__.return_value = mock_transaction
            # Mock the execute method on the existing AIDB instance
            service._aidb.execute = AsyncMock(return_value=mock_result)

            # Mock _execute_with_progress to execute the coroutine directly
            async def execute_directly(coro, desc):
                return await coro

            mock_execute_progress.side_effect = execute_directly

            result = await service.execute_view("user_summary", None)

            assert result.success is True
            assert result.data == [{"summary": "data"}]

            mock_transaction.operation_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_view_with_parameters(self, service):
        """Test view execution with parameters."""
        mock_transaction = AsyncMock()
        mock_result = MagicMock()
        mock_result.status = True
        mock_result.data = None
        mock_result.schema = None
        mock_result.data_loss_indicator = MagicMock()
        mock_result.data_loss_indicator.value = "none"
        mock_result.ai_comment = None
        mock_result.compiled_plan = None
        mock_result.transaction_id = None
        mock_result.error = None
        mock_result.execution_time = None

        with (
            patch("ai_hub.service.git_layer.begin") as mock_begin,
            patch.object(service, "_execute_with_progress") as mock_execute_progress,
        ):

            mock_begin.return_value.__aenter__.return_value = mock_transaction
            # Mock the execute method on the existing AIDB instance
            service._aidb.execute = AsyncMock(return_value=mock_result)

            # Mock _execute_with_progress to execute the coroutine directly
            async def execute_directly(coro, desc):
                return await coro

            mock_execute_progress.side_effect = execute_directly

            parameters = {"user_id": 123, "status": "active"}
            await service.execute_view("user_details", parameters)

            # Check that the query was constructed with parameters
            call_args = service._aidb.execute.call_args
            query = call_args[1]["query"]
            assert "user_details" in query
            assert "user_id=123" in query
            assert "status=active" in query

    @pytest.mark.asyncio
    async def test_execute_data_modification(self, service):
        """Test data modification execution."""
        mock_transaction = AsyncMock()
        mock_result = MagicMock()
        mock_result.status = True
        mock_result.data = None
        mock_result.schema = None
        mock_result.data_loss_indicator = MagicMock()
        mock_result.data_loss_indicator.value = "none"
        mock_result.ai_comment = None
        mock_result.compiled_plan = None
        mock_result.transaction_id = None
        mock_result.error = None
        mock_result.execution_time = None

        with (
            patch("ai_hub.service.git_layer.begin") as mock_begin,
            patch.object(service, "_execute_with_progress") as mock_execute_progress,
        ):

            mock_begin.return_value.__aenter__.return_value = mock_transaction
            # Mock the execute method on the existing AIDB instance
            service._aidb.execute = AsyncMock(return_value=mock_result)

            # Mock _execute_with_progress to execute the coroutine directly
            async def execute_directly(coro, desc):
                return await coro

            mock_execute_progress.side_effect = execute_directly

            operation = "INSERT INTO users (name) VALUES ('John')"
            result = await service.execute_data_modification(operation, PermissionLevel.DATA_MODIFY)

            assert result.success is True

            # Check that write escalation was called
            mock_transaction.write_escalation_required.assert_called_once()
            mock_transaction.operation_complete.assert_called_once()
