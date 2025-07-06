"""Integration tests for AI-Hub using testcontainers."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from testcontainers.compose import DockerCompose


@pytest.fixture(scope="session")
def temp_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()

        # Initialize git repository
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        yield str(repo_path)


@pytest.fixture(scope="session")
def docker_compose_file():
    """Create docker-compose file for integration testing."""
    compose_content = """
version: '3.8'
services:
  ai-hub:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AI_HUB_GIT_REPO_PATH=/data/repos
      - AI_HUB_AIDB_API_KEY=mock-api-key
      - AI_HUB_AIDB_LOG_LEVEL=DEBUG
    volumes:
      - ./test_data:/data/repos
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(compose_content)
        f.flush()
        return f.name


@pytest.mark.integration
class TestAIHubIntegration:
    """Integration tests for AI-Hub service."""

    @pytest.fixture
    def ai_hub_service(self, docker_compose_file, temp_repo):
        """Start AI-Hub service in container."""
        # Create test data directory
        test_data_dir = Path(temp_repo).parent / "test_data"
        test_data_dir.mkdir(exist_ok=True)

        # Copy test repo to test data directory
        import shutil
        shutil.copytree(temp_repo, test_data_dir / "test_repo")

        with DockerCompose(
            filepath=docker_compose_file,
            compose_file_name="docker-compose.test.yml"
        ) as compose:
            # Wait for service to be healthy
            service_url = f"http://localhost:{compose.get_service_port('ai-hub', 8000)}"

            # Wait for health check
            import time
            max_retries = 30
            for _ in range(max_retries):
                try:
                    response = requests.get(f"{service_url}/health", timeout=5)
                    if response.status_code == 200:
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(2)
            else:
                pytest.fail("AI-Hub service did not become healthy")

            yield service_url

    def test_service_health(self, ai_hub_service):
        """Test service health endpoint."""
        response = requests.get(f"{ai_hub_service}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "git_repo_path" in data
        assert "repo_exists" in data

    def test_service_root(self, ai_hub_service):
        """Test service root endpoint."""
        response = requests.get(ai_hub_service)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "AI-Hub API Server"
        assert data["version"] == "0.1.0"

    def test_api_documentation(self, ai_hub_service):
        """Test API documentation endpoint."""
        response = requests.get(f"{ai_hub_service}/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_spec(self, ai_hub_service):
        """Test OpenAPI specification endpoint."""
        response = requests.get(f"{ai_hub_service}/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        assert spec["info"]["title"] == "AI-Hub"
        assert "paths" in spec
        assert "/api/v1/db/query" in spec["paths"]
        assert "/api/v1/db/query/view" in spec["paths"]
        assert "/api/v1/db/data" in spec["paths"]


@pytest.mark.integration
class TestAIHubAPIMocked:
    """Integration tests with mocked AI services."""

    @pytest.fixture
    def mock_ai_responses(self):
        """Mock AI service responses."""
        with patch('ai_db.core.ai_agent.AIAgent') as mock_agent:
            mock_instance = mock_agent.return_value

            # Mock successful query response
            mock_instance.process_query.return_value = {
                "success": True,
                "data": [{"id": 1, "name": "Test User"}],
                "schema": {"users": {"id": "integer", "name": "string"}},
                "compiled_plan": "SELECT id, name FROM users",
                "ai_comment": "Query executed successfully"
            }

            yield mock_instance

    def test_query_execution_mocked(self, ai_hub_service, mock_ai_responses):
        """Test query execution with mocked AI responses."""
        query_data = {
            "query": "Show me all users",
            "permissions": "select"
        }

        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )

        # Should succeed with mocked responses
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_view_execution_mocked(self, ai_hub_service, mock_ai_responses):
        """Test view execution with mocked AI responses."""
        view_data = {
            "view_name": "user_summary"
        }

        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query/view",
            json=view_data,
            headers={"Content-Type": "application/json"}
        )

        # Should succeed with mocked responses
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_data_modification_mocked(self, ai_hub_service, mock_ai_responses):
        """Test data modification with mocked AI responses."""
        modification_data = {
            "operation": "INSERT INTO users (name) VALUES ('New User')",
            "permissions": "data_modify"
        }

        response = requests.post(
            f"{ai_hub_service}/api/v1/db/data",
            json=modification_data,
            headers={"Content-Type": "application/json"}
        )

        # Should succeed with mocked responses
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""

    def test_invalid_json(self, ai_hub_service):
        """Test handling of invalid JSON."""
        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Validation error

    def test_missing_fields(self, ai_hub_service):
        """Test handling of missing required fields."""
        # Missing query field
        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query",
            json={"permissions": "select"},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_invalid_permission_level(self, ai_hub_service):
        """Test handling of invalid permission levels."""
        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query",
            json={
                "query": "SELECT * FROM users",
                "permissions": "invalid_permission"
            },
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_cors_headers(self, ai_hub_service):
        """Test CORS headers are present."""
        response = requests.options(
            f"{ai_hub_service}/api/v1/db/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Should handle CORS preflight
        assert response.status_code in [200, 405]

        # Test actual request with origin
        response = requests.post(
            f"{ai_hub_service}/api/v1/db/query",
            json={
                "query": "SELECT 1",
                "permissions": "select"
            },
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            }
        )

        # CORS headers should be present (exact headers depend on FastAPI CORS config)
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
