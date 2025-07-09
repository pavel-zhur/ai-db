"""Simplified integration tests using AI stub."""

from pathlib import Path

import pytest

from ai_db import AIDB, PermissionLevel
from tests.conftest import MockTransactionContext


@pytest.mark.integration
class TestQueryExecutionSimple:
    """Test end-to-end query execution with AI stub."""

    @pytest.mark.asyncio
    async def test_create_table(self, temp_dir: Path):
        """Test creating a table."""
        # Create mock transaction
        transaction = MockTransactionContext("test-txn", str(temp_dir))

        # Create database - stub AI agent injected automatically
        db = AIDB()

        # Execute create table
        result = await db.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE)",
            PermissionLevel.SCHEMA_MODIFY,
            transaction,
        )

        assert result.status is True
        assert result.error is None
        assert result.data_loss_indicator.value == "none"

    @pytest.mark.asyncio
    async def test_permission_denied(self, temp_dir: Path):
        """Test permission denied for schema modification."""
        # Create mock transaction
        transaction = MockTransactionContext("test-txn", str(temp_dir))

        # Create database
        db = AIDB()

        # Execute with insufficient permissions
        result = await db.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY)",
            PermissionLevel.SELECT,  # Not enough permission for schema_modify
            transaction,
        )

        assert result.status is False
        assert "permission" in result.error.lower() or "PermissionError" in result.error

    @pytest.mark.asyncio
    async def test_select_query(self, temp_dir: Path):
        """Test SELECT query compilation."""
        # Create mock transaction
        transaction = MockTransactionContext("test-txn", str(temp_dir))

        # Create database
        db = AIDB()

        # Execute select query
        result = await db.execute("SELECT * FROM users", PermissionLevel.SELECT, transaction)

        assert result.status is True
        assert result.error is None
        assert result.compiled_plan is not None

    @pytest.mark.asyncio
    async def test_execute_compiled_query(self, temp_dir: Path):
        """Test executing a compiled query plan."""
        # Create mock transaction
        transaction = MockTransactionContext("test-txn", str(temp_dir))

        # Create database
        db = AIDB()

        # First compile a query
        result = await db.execute("SELECT * FROM users", PermissionLevel.SELECT, transaction)

        assert result.status is True
        assert result.compiled_plan is not None

        # Execute the compiled plan
        compiled_result = db.execute_compiled(result.compiled_plan, transaction)

        assert compiled_result.status is True
        assert compiled_result.data is not None
        assert isinstance(compiled_result.data, list)
