"""Integration tests for AI-Frontend MCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import mcp.types as types

from src.ai_frontend_server import create_ai_frontend_server
from src.config import AIFrontendConfig


class TestAIFrontendServer:
    """Integration tests for AI-Frontend server."""
    
    @pytest.mark.asyncio
    async def test_server_creation(self, ai_frontend_config):
        """Test server creation with mocks."""
        server = await create_ai_frontend_server(ai_frontend_config)
        assert server is not None
        assert server.name == "ai-frontend-mcp-server"
    
    @pytest.mark.asyncio
    async def test_list_tools(self, ai_frontend_config):
        """Test listing available tools."""
        server = await create_ai_frontend_server(ai_frontend_config)
        
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
        assert "generate_frontend" in tool_names
        assert "get_frontend_info" in tool_names
        
        # Check tool properties
        generate_tool = next(t for t in tools if t.name == "generate_frontend")
        assert generate_tool.description == "Generate or modify React frontend components using natural language"
        assert generate_tool.destructiveHint is True
        assert generate_tool.readOnlyHint is False
        
        info_tool = next(t for t in tools if t.name == "get_frontend_info")
        assert info_tool.destructiveHint is False
        assert info_tool.readOnlyHint is True
    
    @pytest.mark.asyncio
    async def test_call_generate_frontend(self, ai_frontend_config):
        """Test calling the generate_frontend tool."""
        server = await create_ai_frontend_server(ai_frontend_config)
        
        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break
        
        assert call_tool_handler is not None
        
        # Call generate_frontend tool
        result = await call_tool_handler(
            "generate_frontend",
            {"request": "Create a user dashboard with charts"}
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "success" in result[0].text
        assert "Dashboard" in result[0].text
        assert result[0].isError is False
    
    @pytest.mark.asyncio
    async def test_call_get_frontend_info(self, ai_frontend_config):
        """Test calling the get_frontend_info tool."""
        server = await create_ai_frontend_server(ai_frontend_config)
        
        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break
        
        # Call get_frontend_info tool
        result = await call_tool_handler("get_frontend_info", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "UserList" in result[0].text
        assert "UserForm" in result[0].text
        assert result[0].isError is False
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ai_frontend_config):
        """Test error handling for invalid requests."""
        server = await create_ai_frontend_server(ai_frontend_config)
        
        # Get the call_tool handler
        call_tool_handler = None
        for handler in server._handlers:
            if handler[0] == "tools/call":
                call_tool_handler = handler[1]
                break
        
        # Call with missing required parameter
        result = await call_tool_handler("generate_frontend", {})
        
        assert len(result) == 1
        assert result[0].isError is True
        assert "Tool execution failed" in result[0].text