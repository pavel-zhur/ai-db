"""Test console interface."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from console.console_interface import ConsoleInterface
from console.models import CommandType, OutputFormat


@pytest.fixture
def mock_dependencies(
    test_config: Any,
    console: Any,
    trace_logger: Any,
    command_parser: Any,
    output_formatter: Any,
    session_state: Any,
) -> dict[str, Any]:
    """Create console interface with mocked dependencies."""
    return {
        "config": test_config,
        "console": console,
        "trace_logger": trace_logger,
        "command_parser": command_parser,
        "output_formatter": output_formatter,
        "session_state": session_state,
    }


@pytest.fixture
def console_interface(mock_dependencies: dict[str, Any]) -> ConsoleInterface:
    """Create console interface instance."""
    return ConsoleInterface(**mock_dependencies)


class TestConsoleInterface:
    """Test console interface functionality."""

    @pytest.mark.asyncio
    async def test_begin_transaction(
        self, console_interface: ConsoleInterface, mock_git_transaction: AsyncMock
    ) -> None:
        """Test beginning a transaction."""
        with (
            patch("console.console_interface.git_layer.begin", return_value=mock_git_transaction),
            patch("console.console_interface.AIDB") as mock_aidb_class,
            patch("console.console_interface.AiFrontend") as mock_frontend_class,
        ):
            # Mock the classes
            mock_aidb_class.return_value = MagicMock()
            mock_frontend_class.return_value = MagicMock()

            await console_interface._begin_transaction()

            assert console_interface._session_state.transaction_active is True
            assert console_interface._session_state.transaction_id == mock_git_transaction.id
            assert console_interface._git_transaction is not None
            assert console_interface._ai_db is not None
            assert console_interface._ai_frontend is not None

    @pytest.mark.asyncio
    async def test_begin_transaction_already_active(
        self, console_interface: ConsoleInterface
    ) -> None:
        """Test beginning transaction when one is already active."""
        console_interface._session_state.transaction_active = True

        await console_interface._begin_transaction()

        # Should not create new transaction
        assert console_interface._git_transaction is None

    @pytest.mark.asyncio
    async def test_commit_transaction(
        self, console_interface: ConsoleInterface, mock_git_transaction: AsyncMock
    ) -> None:
        """Test committing a transaction."""
        # Setup active transaction
        console_interface._session_state.transaction_active = True
        console_interface._session_state.transaction_id = "test"
        console_interface._git_transaction = mock_git_transaction
        console_interface._ai_db = MagicMock()
        console_interface._ai_frontend = MagicMock()

        await console_interface._commit_transaction()

        assert console_interface._session_state.transaction_active is False
        assert console_interface._session_state.transaction_id is None
        assert console_interface._git_transaction is None
        assert console_interface._ai_db is None
        assert console_interface._ai_frontend is None

        # Verify git transaction was exited properly
        mock_git_transaction.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_rollback_transaction(
        self, console_interface: ConsoleInterface, mock_git_transaction: AsyncMock
    ) -> None:
        """Test rolling back a transaction."""
        # Setup active transaction
        console_interface._session_state.transaction_active = True
        console_interface._session_state.transaction_id = "test"
        console_interface._git_transaction = mock_git_transaction
        console_interface._ai_db = MagicMock()
        console_interface._ai_frontend = MagicMock()

        await console_interface._rollback_transaction()

        assert console_interface._session_state.transaction_active is False
        assert console_interface._session_state.transaction_id is None
        assert console_interface._git_transaction is None
        assert console_interface._ai_db is None
        assert console_interface._ai_frontend is None

        # Verify git transaction was exited with exception
        mock_git_transaction.__aexit__.assert_called_once()
        args = mock_git_transaction.__aexit__.call_args[0]
        assert args[0] is Exception

    @pytest.mark.asyncio
    async def test_execute_db_query(
        self,
        console_interface: ConsoleInterface,
        mock_ai_db: AsyncMock,
        mock_git_transaction: AsyncMock,
    ) -> None:
        """Test executing a database query."""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "name": "Test"}]
        mock_result.ai_comment = "Found 1 result"
        mock_result.compiled_plan = None
        mock_ai_db.execute.return_value = mock_result

        # Setup transaction
        console_interface._session_state.transaction_active = True
        console_interface._git_transaction = mock_git_transaction
        console_interface._ai_db = mock_ai_db

        await console_interface._execute_db_query(CommandType.QUERY, "SELECT * FROM users")

        # Verify AI-DB was called
        mock_ai_db.execute.assert_called_once()
        call_args = mock_ai_db.execute.call_args[1]
        assert call_args["query"] == "SELECT * FROM users"
        assert call_args["permissions"].value == "select"
        assert call_args["transaction"] == mock_git_transaction

        # Verify result was added to history
        assert len(console_interface._session_state.conversation_history) == 1
        entry = console_interface._session_state.conversation_history[0]
        assert entry.user_input == "SELECT * FROM users"
        assert entry.command_type == CommandType.QUERY

    @pytest.mark.asyncio
    async def test_generate_frontend(
        self,
        console_interface: ConsoleInterface,
        mock_ai_db: AsyncMock,
        mock_ai_frontend: AsyncMock,
        mock_git_transaction: AsyncMock,
    ) -> None:
        """Test generating frontend."""
        # Setup mocks
        schema_result = MagicMock()
        schema_result.data = {"tables": ["users", "products"]}
        mock_ai_db.execute.return_value = schema_result

        frontend_result = MagicMock()
        frontend_result.success = True
        frontend_result.output_path = "/output/frontend"
        mock_ai_frontend.generate_frontend.return_value = frontend_result

        # Setup transaction
        console_interface._session_state.transaction_active = True
        console_interface._git_transaction = mock_git_transaction
        console_interface._ai_db = mock_ai_db
        console_interface._ai_frontend = mock_ai_frontend

        await console_interface._generate_frontend("Create a dashboard")

        # Verify schema was fetched
        mock_ai_db.execute.assert_called_once()

        # Verify frontend was generated
        mock_ai_frontend.generate_frontend.assert_called_once()
        call_args = mock_ai_frontend.generate_frontend.call_args[1]
        assert call_args["request"] == "Create a dashboard"
        assert call_args["schema"] == schema_result.data
        assert call_args["transaction"] == mock_git_transaction
        assert call_args["project_name"] == "console-frontend"

    def test_set_output_format(self, console_interface: ConsoleInterface) -> None:
        """Test setting output format."""
        # Test JSON format
        console_interface._set_output_format("json")
        assert console_interface._session_state.current_output_format == OutputFormat.JSON

        # Test YAML format
        console_interface._set_output_format("yaml")
        assert console_interface._session_state.current_output_format == OutputFormat.YAML

        # Test table format
        console_interface._set_output_format("table")
        assert console_interface._session_state.current_output_format == OutputFormat.TABLE

        # Test invalid format should not change
        console_interface._set_output_format("invalid")
        assert console_interface._session_state.current_output_format == OutputFormat.TABLE

    @pytest.mark.asyncio
    async def test_handle_command_exit(self, console_interface: ConsoleInterface) -> None:
        """Test handling exit command."""
        with pytest.raises(KeyboardInterrupt):
            await console_interface._handle_command(CommandType.EXIT, None, "exit")

    @pytest.mark.asyncio
    async def test_handle_command_with_error(self, console_interface: ConsoleInterface) -> None:
        """Test handling command that raises error."""
        # Mock method to raise error
        with patch.object(
            console_interface, "_execute_db_query", AsyncMock(side_effect=Exception("Test error"))
        ):
            await console_interface._handle_command(CommandType.QUERY, None, "SELECT * FROM users")

            # Verify error was logged
            assert len(console_interface._session_state.conversation_history) == 1
            entry = console_interface._session_state.conversation_history[0]
            assert entry.error == "Test error"
            assert entry.user_input == "SELECT * FROM users"
