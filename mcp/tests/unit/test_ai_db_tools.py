"""Unit tests for AI-DB tools."""

import pytest

from ai_mcp.models.ai_db import (
    PermissionLevel,
)
from ai_mcp.tools.ai_db import (
    DataModifyTool,
    GetSchemaTool,
    SchemaModifyTool,
    SelectTool,
)


class TestSchemaModifyTool:
    """Test schema modification tool."""

    @pytest.mark.asyncio
    async def test_schema_modify_success(
        self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger
    ):
        """Test successful schema modification."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"query": "CREATE TABLE products (id INT, name TEXT)"}
        response = await tool.execute(params)

        assert response["success"] is True
        assert response.get("error") is None

    @pytest.mark.asyncio
    async def test_schema_modify_with_transaction(
        self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger
    ):
        """Test schema modification within transaction."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"query": "ALTER TABLE users ADD COLUMN age INT"}
        response = await tool.execute(params)

        assert response["success"] is True

    def test_tool_properties(self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger):
        """Test tool properties."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        assert tool.name == "schema_modify"
        assert tool.permission_level == PermissionLevel.SCHEMA_MODIFY
        assert tool.destructive_hint is True
        assert tool.read_only_hint is False


class TestDataModifyTool:
    """Test data modification tool."""

    @pytest.mark.asyncio
    async def test_data_modify_success(self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger):
        """Test successful data modification."""
        tool = DataModifyTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"query": "INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')"}
        response = await tool.execute(params)

        assert response["success"] is True


class TestSelectTool:
    """Test select query tool."""

    @pytest.mark.asyncio
    async def test_select_success(self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger):
        """Test successful select query."""
        tool = SelectTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"query": "SELECT * FROM users"}
        response = await tool.execute(params)

        assert response["success"] is True
        assert response["data"] is not None
        assert len(response["data"]) == 2

    def test_tool_properties(self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger):
        """Test tool properties."""
        tool = SelectTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        assert tool.name == "select"
        assert tool.permission_level == PermissionLevel.SELECT
        assert tool.destructive_hint is False
        assert tool.read_only_hint is True


# NOTE: Transaction tools have been replaced with ai-shared.TransactionProtocol
# class TestTransactionTools:
#     """Test transaction-related tools."""
#     # Test cases commented out - transaction management is now handled
#     # by ai-shared.TransactionProtocol and git-layer integration


class TestIntrospectionTools:
    """Test introspection tools."""

    @pytest.mark.asyncio
    async def test_get_schema(self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger):
        """Test getting schema."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"include_documentation": True}
        response = await tool.execute(params)

        assert response["success"] is True
        assert response["schema"]["tables"] is not None
        assert "users" in response["schema"]["tables"]

    @pytest.mark.asyncio
    async def test_get_schema_without_docs(
        self, mock_ai_db, mock_git_layer, ai_db_config, mock_logger
    ):
        """Test getting schema without semantic docs."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, ai_db_config, mock_logger)

        params = {"include_documentation": False}
        response = await tool.execute(params)

        assert response["success"] is True
        assert response["schema"]["tables"] is not None
