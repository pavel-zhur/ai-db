"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

from ai_db.core.models import TransactionContext
from ai_db.transaction.context import MockTransactionContext


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def transaction_context(temp_dir: Path) -> TransactionContext:
    """Create a mock transaction context."""
    return MockTransactionContext(
        transaction_id="test-txn-123",
        working_directory=str(temp_dir)
    )


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