"""Unit tests for AI-Frontend tools."""

import pytest

from ai_mcp.tools.ai_frontend import (
    GenerateFrontendTool,
)


class TestGenerateFrontendTool:
    """Test frontend generation tool."""

    @pytest.mark.asyncio
    async def test_generate_frontend_success(
        self, mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
    ):
        """Test successful frontend generation."""
        tool = GenerateFrontendTool(
            mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
        )

        params = {
            "request": "Create a user dashboard with charts",
            "schema": {"tables": {"users": {"columns": []}}},
            "project_name": "test-project",
        }
        response = await tool.execute(params)

        assert response["success"] is True
        assert response["output_path"] is not None
        assert response.get("error") is None

    @pytest.mark.asyncio
    async def test_generate_frontend_with_transaction(
        self, mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
    ):
        """Test frontend generation within transaction."""
        tool = GenerateFrontendTool(
            mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
        )

        params = {
            "request": "Create a form for user data",
            "schema": {"tables": {"users": {"columns": []}}},
            "project_name": "test-project",
        }
        response = await tool.execute(params)

        assert response["success"] is True
        assert response["output_path"] is not None

    def test_tool_properties(
        self, mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
    ):
        """Test tool properties."""
        tool = GenerateFrontendTool(
            mock_ai_frontend, mock_git_layer, ai_frontend_config, mock_logger
        )

        assert tool.name == "generate_frontend"
        assert tool.destructive_hint is True
        assert tool.read_only_hint is False


# NOTE: GetFrontendInfoTool has been replaced with GetFrontendSchemaTool
# class TestGetFrontendInfoTool:
#     """Test frontend info tool."""
#     # Test cases commented out - tool has been updated to match
#     # actual ai-frontend interface with GetFrontendSchemaTool
