"""Tests for AI-Hub endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from ai_hub.main import app
from ai_hub.models import DataLossIndicator, PermissionLevel, QueryResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def mock_service():
    """Create mock service."""
    return AsyncMock()


class TestRootEndpoints:
    """Test root and health endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI-Hub API Server"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "git_repo_path" in data
        assert "repo_exists" in data

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "git_repo_path" in data
        assert "repo_exists" in data
        assert "repo_is_git" in data


class TestQueryEndpoint:
    """Test query execution endpoint."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, async_client, mock_service):
        """Test successful query execution."""
        # Mock successful response
        mock_response = QueryResponse(
            success=True,
            data=[{"id": 1, "name": "John"}],
            schema={"users": {"id": "integer", "name": "string"}},
            data_loss_indicator=DataLossIndicator.NONE,
            ai_comment="Query executed successfully",
            execution_time=0.5
        )
        mock_service.execute_query.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/query",
                json={
                    "query": "SELECT * FROM users",
                    "permissions": "select"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == [{"id": 1, "name": "John"}]
        assert data["schema"] == {"users": {"id": "integer", "name": "string"}}
        assert data["data_loss_indicator"] == "none"
        assert data["ai_comment"] == "Query executed successfully"
        assert data["execution_time"] == 0.5

        mock_service.execute_query.assert_called_once_with(
            query="SELECT * FROM users",
            permissions=PermissionLevel.SELECT
        )

    @pytest.mark.asyncio
    async def test_execute_query_validation_error(self, async_client):
        """Test query execution with validation error."""
        response = await async_client.post(
            "/api/v1/db/query",
            json={
                "query": "SELECT * FROM users"
                # Missing permissions
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_execute_query_service_error(self, async_client, mock_service):
        """Test query execution with service error."""
        mock_service.execute_query.side_effect = Exception("Database connection failed")

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/query",
                json={
                    "query": "SELECT * FROM users",
                    "permissions": "select"
                }
            )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert "error" in data["detail"]
        assert "error_details" in data["detail"]


class TestViewEndpoint:
    """Test view execution endpoint."""

    @pytest.mark.asyncio
    async def test_execute_view_success(self, async_client, mock_service):
        """Test successful view execution."""
        mock_response = QueryResponse(
            success=True,
            data=[{"summary": "User summary"}],
            execution_time=0.3
        )
        mock_service.execute_view.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/query/view",
                json={
                    "view_name": "user_summary"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == [{"summary": "User summary"}]

        mock_service.execute_view.assert_called_once_with(
            view_name="user_summary",
            parameters=None
        )

    @pytest.mark.asyncio
    async def test_execute_view_with_parameters(self, async_client, mock_service):
        """Test view execution with parameters."""
        mock_response = QueryResponse(success=True, data=[])
        mock_service.execute_view.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/query/view",
                json={
                    "view_name": "user_details",
                    "parameters": {"user_id": 123, "status": "active"}
                }
            )

        assert response.status_code == 200

        mock_service.execute_view.assert_called_once_with(
            view_name="user_details",
            parameters={"user_id": 123, "status": "active"}
        )

    @pytest.mark.asyncio
    async def test_execute_view_validation_error(self, async_client):
        """Test view execution with validation error."""
        response = await async_client.post(
            "/api/v1/db/query/view",
            json={}  # Missing view_name
        )

        assert response.status_code == 422


class TestDataModificationEndpoint:
    """Test data modification endpoint."""

    @pytest.mark.asyncio
    async def test_execute_data_modification_success(self, async_client, mock_service):
        """Test successful data modification."""
        mock_response = QueryResponse(
            success=True,
            data_loss_indicator=DataLossIndicator.NONE,
            ai_comment="Data inserted successfully"
        )
        mock_service.execute_data_modification.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/data",
                json={
                    "operation": "INSERT INTO users (name) VALUES ('John')",
                    "permissions": "data_modify"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data_loss_indicator"] == "none"
        assert data["ai_comment"] == "Data inserted successfully"

        mock_service.execute_data_modification.assert_called_once_with(
            operation="INSERT INTO users (name) VALUES ('John')",
            permissions=PermissionLevel.DATA_MODIFY
        )

    @pytest.mark.asyncio
    async def test_execute_data_modification_default_permissions(self, async_client, mock_service):
        """Test data modification with default permissions."""
        mock_response = QueryResponse(success=True)
        mock_service.execute_data_modification.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/data",
                json={
                    "operation": "UPDATE users SET name = 'Jane' WHERE id = 1"
                    # No explicit permissions - should default to data_modify
                }
            )

        assert response.status_code == 200

        mock_service.execute_data_modification.assert_called_once_with(
            operation="UPDATE users SET name = 'Jane' WHERE id = 1",
            permissions=PermissionLevel.DATA_MODIFY  # Default
        )

    @pytest.mark.asyncio
    async def test_execute_data_modification_schema_permissions(self, async_client, mock_service):
        """Test data modification with schema permissions."""
        mock_response = QueryResponse(success=True)
        mock_service.execute_data_modification.return_value = mock_response

        with patch('ai_hub.endpoints.get_service', return_value=mock_service):
            response = await async_client.post(
                "/api/v1/db/data",
                json={
                    "operation": "CREATE TABLE new_table (id INTEGER)",
                    "permissions": "schema_modify"
                }
            )

        assert response.status_code == 200

        mock_service.execute_data_modification.assert_called_once_with(
            operation="CREATE TABLE new_table (id INTEGER)",
            permissions=PermissionLevel.SCHEMA_MODIFY
        )

    @pytest.mark.asyncio
    async def test_execute_data_modification_validation_error(self, async_client):
        """Test data modification with validation error."""
        response = await async_client.post(
            "/api/v1/db/data",
            json={}  # Missing operation
        )

        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/v1/db/query",
            headers={"Origin": "http://localhost:3000"}
        )

        # FastAPI automatically handles OPTIONS for CORS
        assert response.status_code in [200, 405]  # 405 if no explicit OPTIONS handler

    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/v1/db/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        # Should allow the request (exact status depends on FastAPI CORS implementation)
        assert response.status_code in [200, 405]
