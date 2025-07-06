"""Unit tests for validation and constraints."""


import pytest

from ai_db.core.models import Column, Constraint, ConstraintType, Table
from ai_db.exceptions import ValidationError
from ai_db.validation import ConstraintChecker, DataValidator, SafeExecutor


class TestDataValidator:
    """Test data validation."""

    def test_validate_valid_row(self):
        """Test validating a valid row."""
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="name", type="string", nullable=False),
                Column(name="age", type="integer", nullable=True),
            ]
        )

        validator = DataValidator()
        row = {"id": 1, "name": "Alice", "age": 30}

        # Should not raise
        validator.validate_row(row, table)

    def test_validate_invalid_row_missing_required(self):
        """Test validating row with missing required field."""
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="name", type="string", nullable=False),
            ]
        )

        validator = DataValidator()
        row = {"id": 1}  # Missing required 'name'

        with pytest.raises(ValidationError) as exc:
            validator.validate_row(row, table)

        assert "required" in str(exc.value).lower()

    def test_validate_invalid_row_wrong_type(self):
        """Test validating row with wrong type."""
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="age", type="integer", nullable=False),
            ]
        )

        validator = DataValidator()
        row = {"id": 1, "age": "thirty"}  # Wrong type for age

        with pytest.raises(ValidationError):
            validator.validate_row(row, table)

    def test_validate_rows_multiple_errors(self):
        """Test validating multiple rows returns all errors."""
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="name", type="string", nullable=False),
            ]
        )

        validator = DataValidator()
        rows = [
            {"id": 1},  # Missing name
            {"id": "two", "name": "Bob"},  # Wrong type for id
            {"id": 3, "name": "Charlie"},  # Valid
        ]

        errors = validator.validate_rows(rows, table)
        assert len(errors) == 2
        assert "Row 0" in errors[0]
        assert "Row 1" in errors[1]


class TestConstraintChecker:
    """Test constraint checking."""

    @pytest.mark.asyncio
    async def test_check_primary_key_valid(self):
        """Test primary key constraint with valid data."""
        table = Table(
            name="users",
            columns=[Column(name="id", type="integer", nullable=False)],
            constraints=[
                Constraint(
                    name="pk_users",
                    type=ConstraintType.PRIMARY_KEY,
                    columns=["id"]
                )
            ]
        )

        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(table, data, {"users": data})

        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_check_primary_key_duplicate(self):
        """Test primary key constraint with duplicates."""
        table = Table(
            name="users",
            columns=[Column(name="id", type="integer", nullable=False)],
            constraints=[
                Constraint(
                    name="pk_users",
                    type=ConstraintType.PRIMARY_KEY,
                    columns=["id"]
                )
            ]
        )

        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 1, "name": "Charlie"},  # Duplicate ID
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(table, data, {"users": data})

        assert len(errors) == 1
        assert "Duplicate primary key" in errors[0]

    @pytest.mark.asyncio
    async def test_check_unique_constraint(self):
        """Test unique constraint."""
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="integer"),
                Column(name="email", type="string"),
            ],
            constraints=[
                Constraint(
                    name="uk_email",
                    type=ConstraintType.UNIQUE,
                    columns=["email"]
                )
            ]
        )

        data = [
            {"id": 1, "email": "alice@example.com"},
            {"id": 2, "email": "bob@example.com"},
            {"id": 3, "email": "alice@example.com"},  # Duplicate email
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(table, data, {"users": data})

        assert len(errors) == 1
        assert "Duplicate unique constraint" in errors[0]

    @pytest.mark.asyncio
    async def test_check_foreign_key_valid(self):
        """Test foreign key constraint with valid references."""
        orders_table = Table(
            name="orders",
            columns=[
                Column(name="id", type="integer"),
                Column(name="user_id", type="integer"),
            ],
            constraints=[
                Constraint(
                    name="fk_user",
                    type=ConstraintType.FOREIGN_KEY,
                    columns=["user_id"],
                    referenced_table="users",
                    referenced_columns=["id"]
                )
            ]
        )

        users_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        orders_data = [
            {"id": 1, "user_id": 1},
            {"id": 2, "user_id": 2},
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(
            orders_table,
            orders_data,
            {"users": users_data, "orders": orders_data}
        )

        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_check_foreign_key_invalid(self):
        """Test foreign key constraint with invalid references."""
        orders_table = Table(
            name="orders",
            columns=[
                Column(name="id", type="integer"),
                Column(name="user_id", type="integer"),
            ],
            constraints=[
                Constraint(
                    name="fk_user",
                    type=ConstraintType.FOREIGN_KEY,
                    columns=["user_id"],
                    referenced_table="users",
                    referenced_columns=["id"]
                )
            ]
        )

        users_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        orders_data = [
            {"id": 1, "user_id": 1},
            {"id": 2, "user_id": 99},  # Invalid user_id
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(
            orders_table,
            orders_data,
            {"users": users_data, "orders": orders_data}
        )

        assert len(errors) == 1
        assert "Foreign key violation" in errors[0]

    @pytest.mark.asyncio
    async def test_check_constraint(self):
        """Test CHECK constraint."""
        table = Table(
            name="users",
            columns=[
                Column(name="age", type="integer"),
            ],
            constraints=[
                Constraint(
                    name="chk_age",
                    type=ConstraintType.CHECK,
                    columns=["age"],
                    definition="age >= 0 and age <= 150"
                )
            ]
        )

        data = [
            {"age": 25},  # Valid
            {"age": 0},   # Valid (boundary)
            {"age": 150}, # Valid (boundary)
            {"age": -5},  # Invalid
            {"age": 200}, # Invalid
        ]

        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        errors = await checker.check_constraints(table, data, {"users": data})

        assert len(errors) == 2
        assert "Row 3" in errors[0]
        assert "Row 4" in errors[1]


class TestSafeExecutor:
    """Test safe code execution."""

    @pytest.mark.asyncio
    async def test_execute_safe_function(self):
        """Test executing a safe function."""
        executor = SafeExecutor()

        code = '''
def add_numbers(a, b):
    return a + b
'''

        func = await executor.execute_function(code, "add_numbers")
        assert func is not None
        assert func(2, 3) == 5

    @pytest.mark.asyncio
    async def test_execute_unsafe_function(self):
        """Test that unsafe operations are blocked."""
        executor = SafeExecutor()

        # Try to import (should fail)
        code = '''
import os
def bad_function():
    return os.system("ls")
'''

        func = await executor.execute_function(code, "bad_function")
        assert func is None  # Should fail to compile

    @pytest.mark.asyncio
    async def test_evaluate_expression(self):
        """Test evaluating expressions."""
        executor = SafeExecutor()

        context = {"x": 10, "y": 20}
        result = await executor.evaluate_expression("x + y", context)
        assert result == 30

        result = await executor.evaluate_expression("x > y", context)
        assert result is False
