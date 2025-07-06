"""Integration tests for AI-DB MCP server."""

import pytest

from ai_mcp.ai_db_server import create_ai_db_server


class TestAIDBServer:
    """Integration tests for AI-DB server."""

    @pytest.mark.asyncio
    async def test_server_creation(self, ai_db_config):
        """Test server creation with mocks."""
        server = await create_ai_db_server(ai_db_config)
        assert server is not None
        assert server.name == "ai-db-mcp-server"

    @pytest.mark.asyncio
    async def test_list_tools(self, ai_db_config):
        """Test listing available tools."""
        server = await create_ai_db_server(ai_db_config)

        # Get the list_tools handler
        list_tools_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/list":
                list_tools_handler = handler[1]
                break

        assert list_tools_handler is not None

        # Call the handler
        tools = await list_tools_handler()

        # Verify tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "schema_modify",
            "data_modify",
            "select",
            "view_modify",
            "execute_compiled",
            "begin_transaction",
            "commit_transaction",
            "rollback_transaction",
            "get_schema",
        ]

        for expected in expected_tools:
            assert expected in tool_names

        # Check tool properties
        schema_tool = next(t for t in tools if t.name == "schema_modify")
        assert (
            schema_tool.description == "Modify table schemas, manage relationships, and constraints"
        )
        assert schema_tool.destructiveHint is True
        assert schema_tool.readOnlyHint is False

        select_tool = next(t for t in tools if t.name == "select")
        assert select_tool.destructiveHint is False
        assert select_tool.readOnlyHint is True

    @pytest.mark.asyncio
    async def test_call_select_tool(self, ai_db_config):
        """Test calling the select tool."""
        server = await create_ai_db_server(ai_db_config)

        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break

        assert call_tool_handler is not None

        # Call select tool
        result = await call_tool_handler("select", {"query": "SELECT * FROM users"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "success" in result[0].text
        assert result[0].isError is False

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self, ai_db_config):
        """Test calling an unknown tool."""
        server = await create_ai_db_server(ai_db_config)

        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break

        result = await call_tool_handler("unknown_tool", {})

        assert len(result) == 1
        assert result[0].isError is True
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_transaction_flow(self, ai_db_config):
        """Test transaction flow: begin -> operations -> commit."""
        server = await create_ai_db_server(ai_db_config)

        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break

        # Begin transaction
        begin_result = await call_tool_handler("begin_transaction", {})
        assert "transaction_id" in begin_result[0].text

        # Extract transaction ID (mock format)
        import re

        tx_match = re.search(r"mock-transaction-\d+", begin_result[0].text)
        assert tx_match is not None
        tx_id = tx_match.group()

        # Perform operation within transaction
        select_result = await call_tool_handler(
            "select", {"query": "SELECT * FROM users", "transaction_id": tx_id}
        )
        assert "success" in select_result[0].text

        # Commit transaction
        commit_result = await call_tool_handler(
            "commit_transaction", {"transaction_id": tx_id, "commit_message": "Test commit"}
        )
        assert "success" in commit_result[0].text
