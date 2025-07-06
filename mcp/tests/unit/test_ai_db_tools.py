"""Unit tests for AI-DB tools."""

import pytest

from ai_mcp.models.ai_db import (
    DataLossIndicator,
    PermissionLevel,
    QueryRequest,
    SchemaRequest,
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
    async def test_schema_modify_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful schema modification."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)

        request = QueryRequest(query="CREATE TABLE products (id INT, name TEXT)")
        response = await tool.execute(request)

        assert response.status == "success"
        assert response.ai_comment == "Created new table"
        assert response.data_loss_indicator == DataLossIndicator.NONE

    @pytest.mark.asyncio
    async def test_schema_modify_with_transaction(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test schema modification within transaction."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)
        tool.store_transaction("test-tx-1", {"id": "test-tx-1"})

        request = QueryRequest(
            query="ALTER TABLE users ADD COLUMN age INT", transaction_id="test-tx-1"
        )
        response = await tool.execute(request)

        assert response.status == "success"
        assert response.transaction_id == "test-tx-1"

    def test_tool_properties(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test tool properties."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)

        assert tool.name == "schema_modify"
        assert tool.permission_level == PermissionLevel.SCHEMA_MODIFY
        assert tool.destructive_hint is True
        assert tool.read_only_hint is False


class TestDataModifyTool:
    """Test data modification tool."""

    @pytest.mark.asyncio
    async def test_data_modify_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful data modification."""
        tool = DataModifyTool(mock_ai_db, mock_git_layer, mock_logger)

        request = QueryRequest(
            query="INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')"
        )
        response = await tool.execute(request)

        assert response.status == "success"
        assert response.ai_comment == "Operation completed"


class TestSelectTool:
    """Test select query tool."""

    @pytest.mark.asyncio
    async def test_select_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful select query."""
        tool = SelectTool(mock_ai_db, mock_git_layer, mock_logger)

        request = QueryRequest(query="SELECT * FROM users")
        response = await tool.execute(request)

        assert response.status == "success"
        assert response.data is not None
        assert len(response.data) == 2
        assert response.ai_comment == "Selected all users"

    def test_tool_properties(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test tool properties."""
        tool = SelectTool(mock_ai_db, mock_git_layer, mock_logger)

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
    async def test_get_schema(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test getting schema."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, mock_logger)

        request = SchemaRequest(include_semantic_docs=True)
        response = await tool.execute(request)

        assert response.schema is not None
        assert "tables" in response.schema
        assert response.semantic_docs is not None

    @pytest.mark.asyncio
    async def test_get_schema_without_docs(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test getting schema without semantic docs."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, mock_logger)

        request = SchemaRequest(include_semantic_docs=False)
        response = await tool.execute(request)

        assert response.schema is not None
        assert response.semantic_docs is None
