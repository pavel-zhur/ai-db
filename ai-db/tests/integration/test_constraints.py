"""Integration tests for constraint validation."""

import pytest
from pathlib import Path
import yaml

from ai_db.storage import YAMLStore, SchemaStore
from ai_db.validation import ConstraintChecker, SafeExecutor
from ai_db.core.models import Table, Column, Constraint, ConstraintType
from ai_db.transaction.context import MockTransactionContext


class TestConstraintIntegration:
    """Test constraint validation in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_foreign_key_cascade(self, temp_dir):
        """Test foreign key validation across multiple tables."""
        transaction = MockTransactionContext("test-txn", str(temp_dir))
        
        # Create schemas directory
        schemas_dir = temp_dir / "schemas"
        schemas_dir.mkdir(exist_ok=True)
        
        # Create users table schema
        users_schema = {
            "name": "users",
            "description": "Users table",
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "name", "type": "string", "nullable": False}
            ],
            "constraints": [
                {"name": "pk_users", "type": "primary_key", "columns": ["id"]}
            ]
        }
        
        with open(schemas_dir / "users.schema.yaml", "w") as f:
            yaml.dump(users_schema, f)
        
        # Create orders table schema with foreign key
        orders_schema = {
            "name": "orders",
            "description": "Orders table",
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "user_id", "type": "integer", "nullable": False},
                {"name": "amount", "type": "number", "nullable": False}
            ],
            "constraints": [
                {"name": "pk_orders", "type": "primary_key", "columns": ["id"]},
                {
                    "name": "fk_user",
                    "type": "foreign_key",
                    "columns": ["user_id"],
                    "referenced_table": "users",
                    "referenced_columns": ["id"]
                }
            ]
        }
        
        with open(schemas_dir / "orders.schema.yaml", "w") as f:
            yaml.dump(orders_schema, f)
        
        # Create test data
        tables_dir = temp_dir / "tables"
        tables_dir.mkdir(exist_ok=True)
        
        users_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        with open(tables_dir / "users.yaml", "w") as f:
            yaml.dump(users_data, f)
        
        # Valid orders
        valid_orders = [
            {"id": 1, "user_id": 1, "amount": 100},
            {"id": 2, "user_id": 2, "amount": 200}
        ]
        
        # Test with valid data
        schema_store = SchemaStore(transaction)
        schema = await schema_store.load_schema()
        
        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        
        all_tables_data = {
            "users": users_data,
            "orders": valid_orders
        }
        
        errors = await checker.check_constraints(
            schema.tables["orders"],
            valid_orders,
            all_tables_data
        )
        
        assert len(errors) == 0
        
        # Test with invalid foreign key
        invalid_orders = valid_orders + [
            {"id": 3, "user_id": 99, "amount": 300}  # Invalid user_id
        ]
        
        errors = await checker.check_constraints(
            schema.tables["orders"],
            invalid_orders,
            {"users": users_data, "orders": invalid_orders}
        )
        
        assert len(errors) == 1
        assert "Foreign key violation" in errors[0]
    
    @pytest.mark.asyncio
    async def test_complex_check_constraint(self, temp_dir):
        """Test complex CHECK constraints."""
        transaction = MockTransactionContext("test-txn", str(temp_dir))
        
        # Create a table with complex check constraint
        products_table = Table(
            name="products",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="name", type="string", nullable=False),
                Column(name="price", type="number", nullable=False),
                Column(name="discount_price", type="number", nullable=True),
                Column(name="stock", type="integer", nullable=False)
            ],
            constraints=[
                Constraint(
                    name="pk_products",
                    type=ConstraintType.PRIMARY_KEY,
                    columns=["id"]
                ),
                Constraint(
                    name="chk_price",
                    type=ConstraintType.CHECK,
                    columns=["price"],
                    definition="price > 0"
                ),
                Constraint(
                    name="chk_discount",
                    type=ConstraintType.CHECK,
                    columns=["price", "discount_price"],
                    definition="discount_price is None or (discount_price > 0 and discount_price < price)"
                ),
                Constraint(
                    name="chk_stock",
                    type=ConstraintType.CHECK,
                    columns=["stock"],
                    definition="stock >= 0"
                )
            ]
        )
        
        # Test data with various constraint violations
        test_data = [
            # Valid products
            {"id": 1, "name": "Product A", "price": 100, "discount_price": 80, "stock": 10},
            {"id": 2, "name": "Product B", "price": 50, "discount_price": None, "stock": 0},
            
            # Invalid products
            {"id": 3, "name": "Product C", "price": -10, "discount_price": None, "stock": 5},  # Negative price
            {"id": 4, "name": "Product D", "price": 100, "discount_price": 120, "stock": 5},  # Discount > price
            {"id": 5, "name": "Product E", "price": 100, "discount_price": 80, "stock": -5},  # Negative stock
        ]
        
        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        
        errors = await checker.check_constraints(
            products_table,
            test_data,
            {"products": test_data}
        )
        
        # Should have 3 errors for the invalid products
        assert len(errors) == 3
        assert any("Row 2" in e and "chk_price" in e for e in errors)
        assert any("Row 3" in e and "chk_discount" in e for e in errors)
        assert any("Row 4" in e and "chk_stock" in e for e in errors)
    
    @pytest.mark.asyncio
    async def test_multi_column_unique_constraint(self, temp_dir):
        """Test multi-column unique constraints."""
        transaction = MockTransactionContext("test-txn", str(temp_dir))
        
        # Create a table with multi-column unique constraint
        user_roles_table = Table(
            name="user_roles",
            columns=[
                Column(name="id", type="integer", nullable=False),
                Column(name="user_id", type="integer", nullable=False),
                Column(name="role_id", type="integer", nullable=False),
                Column(name="assigned_at", type="string", nullable=False)
            ],
            constraints=[
                Constraint(
                    name="pk_user_roles",
                    type=ConstraintType.PRIMARY_KEY,
                    columns=["id"]
                ),
                Constraint(
                    name="uk_user_role",
                    type=ConstraintType.UNIQUE,
                    columns=["user_id", "role_id"]  # User can't have same role twice
                )
            ]
        )
        
        # Test data
        test_data = [
            {"id": 1, "user_id": 1, "role_id": 1, "assigned_at": "2024-01-01"},
            {"id": 2, "user_id": 1, "role_id": 2, "assigned_at": "2024-01-02"},
            {"id": 3, "user_id": 2, "role_id": 1, "assigned_at": "2024-01-03"},
            {"id": 4, "user_id": 1, "role_id": 1, "assigned_at": "2024-01-04"},  # Duplicate!
        ]
        
        safe_executor = SafeExecutor()
        checker = ConstraintChecker(safe_executor)
        
        errors = await checker.check_constraints(
            user_roles_table,
            test_data,
            {"user_roles": test_data}
        )
        
        assert len(errors) == 1
        assert "Row 3" in errors[0]
        assert "unique constraint" in errors[0].lower()