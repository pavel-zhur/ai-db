"""Unit tests for AI-Frontend tools."""

import pytest
from src.tools.ai_frontend import GenerateFrontendTool, GetFrontendInfoTool
from src.models.ai_frontend import FrontendRequest


class TestGenerateFrontendTool:
    """Test frontend generation tool."""
    
    @pytest.mark.asyncio
    async def test_generate_frontend_success(self, mock_ai_frontend, mock_git_layer, mock_logger):
        """Test successful frontend generation."""
        tool = GenerateFrontendTool(mock_ai_frontend, mock_git_layer, mock_logger)
        
        request = FrontendRequest(request="Create a user dashboard with charts")
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.generated_files is not None
        assert len(response.generated_files) == 2
        assert response.ai_comment == "Generated dashboard components"
    
    @pytest.mark.asyncio
    async def test_generate_frontend_with_transaction(self, mock_ai_frontend, mock_git_layer, mock_logger):
        """Test frontend generation within transaction."""
        tool = GenerateFrontendTool(mock_ai_frontend, mock_git_layer, mock_logger)
        tool._transactions["test-tx-1"] = {"id": "test-tx-1"}
        
        request = FrontendRequest(
            request="Create a form for user data",
            transaction_id="test-tx-1"
        )
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.transaction_id == "test-tx-1"
        assert response.generated_files == ["/components/UserForm.tsx"]
    
    def test_tool_properties(self, mock_ai_frontend, mock_git_layer, mock_logger):
        """Test tool properties."""
        tool = GenerateFrontendTool(mock_ai_frontend, mock_git_layer, mock_logger)
        
        assert tool.name == "generate_frontend"
        assert tool.destructive_hint is True
        assert tool.read_only_hint is False


class TestGetFrontendInfoTool:
    """Test frontend info tool."""
    
    @pytest.mark.asyncio
    async def test_get_frontend_info_success(self, mock_ai_frontend, mock_logger):
        """Test getting frontend info."""
        tool = GetFrontendInfoTool(mock_ai_frontend, mock_logger)
        
        response = await tool.execute({})
        
        assert len(response.components) == 2
        assert response.semantic_docs is not None
        assert "UserList" in response.semantic_docs
    
    def test_tool_properties(self, mock_ai_frontend, mock_logger):
        """Test tool properties."""
        tool = GetFrontendInfoTool(mock_ai_frontend, mock_logger)
        
        assert tool.name == "get_frontend_info"
        assert tool.destructive_hint is False
        assert tool.read_only_hint is True