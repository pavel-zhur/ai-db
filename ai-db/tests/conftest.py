"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

from pathlib import Path as PathType
from unittest.mock import AsyncMock
from ai_shared.protocols import TransactionProtocol
from ai_db.core.ai_agent_stub import AIAgentStub


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def transaction_context(temp_dir: Path) -> TransactionProtocol:
    """Create a mock transaction context."""
    mock = AsyncMock(spec=TransactionProtocol)
    mock.id = "test-txn-123"
    mock.path = temp_dir
    mock.write_escalation_required = AsyncMock(return_value=None)
    mock.operation_complete = AsyncMock(return_value=None)
    mock.operation_failed = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def sample_schema() -> Dict[str, Any]:
    """Sample schema for testing."""
    return {
        "name": "users",
        "description": "User accounts table",
        "columns": [
            {
                "name": "id",
                "type": "integer",
                "nullable": False,
                "description": "User ID"
            },
            {
                "name": "username",
                "type": "string",
                "nullable": False,
                "description": "Username"
            },
            {
                "name": "email",
                "type": "string",
                "nullable": False,
                "description": "Email address"
            },
            {
                "name": "age",
                "type": "integer",
                "nullable": True,
                "description": "User age"
            },
            {
                "name": "is_active",
                "type": "boolean",
                "nullable": False,
                "default": True,
                "description": "Account status"
            }
        ],
        "constraints": [
            {
                "name": "pk_users",
                "type": "primary_key",
                "columns": ["id"]
            },
            {
                "name": "uk_username",
                "type": "unique",
                "columns": ["username"]
            },
            {
                "name": "uk_email",
                "type": "unique",
                "columns": ["email"]
            },
            {
                "name": "chk_age",
                "type": "check",
                "columns": ["age"],
                "definition": "age >= 0 and age <= 150"
            }
        ]
    }


@pytest.fixture
def sample_data() -> list[Dict[str, Any]]:
    """Sample user data for testing."""
    return [
        {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
            "age": 30,
            "is_active": True
        },
        {
            "id": 2,
            "username": "bob",
            "email": "bob@example.com",
            "age": 25,
            "is_active": True
        },
        {
            "id": 3,
            "username": "charlie",
            "email": "charlie@example.com",
            "age": None,
            "is_active": False
        }
    ]


@pytest.fixture
def mock_ai_response() -> Dict[str, Any]:
    """Mock AI response for testing."""
    return {
        "operation_type": "select",
        "permission_level": "select",
        "affected_tables": ["users"],
        "requires_python_generation": True,
        "data_loss_indicator": "none",
        "confidence": 0.95,
        "interpretation": "Select all users from the users table"
    }


@pytest.fixture
def stub_ai_agent():
    """Provide AI agent stub for tests."""
    return AIAgentStub()


@pytest.fixture(autouse=True)
def use_ai_stub(monkeypatch):
    """Automatically use AI stub for all tests."""
    # Replace AIAgent imports wherever they're used
    monkeypatch.setattr('ai_db.core.engine.AIAgent', AIAgentStub)
    
    # Also ensure the dependency injection container uses the stub
    from ai_db.core.engine import DIContainer
    from dependency_injector import providers
    
    # Override the AI agent provider
    DIContainer.ai_agent.override(providers.Singleton(AIAgentStub))


# Mock transaction context for integration tests
class MockTransactionContext:
    """Mock transaction context for integration tests."""
    
    def __init__(self, transaction_id: str, path: str):
        self.id = transaction_id
        self.path = path
        self._write_escalated = False
    
    async def write_escalation_required(self) -> None:
        """Mock write escalation."""
        self._write_escalated = True
    
    async def operation_complete(self, operation_type: str) -> None:
        """Mock operation completion."""
        pass
    
    async def operation_failed(self, error: str) -> None:
        """Mock operation failure."""
        pass