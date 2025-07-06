"""Unit tests for query compilation."""

import pytest

from ai_db.core.query_compiler import QueryCompiler
from ai_db.exceptions import CompilationError


class TestQueryCompiler:
    """Test query compilation and execution."""

    def test_compile_valid_query(self):
        """Test compiling a valid query."""
        compiler = QueryCompiler()

        code = '''
def query_select(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", False)]
'''

        compiled = compiler.compile_query(code)
        assert compiled is not None
        assert isinstance(compiled, str)

    def test_compile_invalid_syntax(self):
        """Test compiling query with syntax error."""
        compiler = QueryCompiler()

        code = '''
def query_select(tables):
    users = tables.get("users", [])
    return [u for u in users if  # Syntax error
'''

        with pytest.raises(CompilationError) as exc:
            compiler.compile_query(code)

        assert "Syntax error" in str(exc.value)

    def test_compile_forbidden_import(self):
        """Test that imports are forbidden."""
        compiler = QueryCompiler()

        code = '''
import os
def query_select(tables):
    return []
'''

        with pytest.raises(CompilationError) as exc:
            compiler.compile_query(code)

        assert "Import statements are not allowed" in str(exc.value)

    def test_compile_no_function(self):
        """Test that code must define a function."""
        compiler = QueryCompiler()

        code = '''
# Just a comment, no function
result = []
'''

        with pytest.raises(CompilationError) as exc:
            compiler.compile_query(code)

        assert "must define at least one function" in str(exc.value)

    def test_execute_compiled_query(self):
        """Test executing a compiled query."""
        compiler = QueryCompiler()

        code = '''
def query_active_users(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", False)]
'''

        # Compile
        compiled = compiler.compile_query(code)

        # Execute
        table_data = {
            "users": [
                {"id": 1, "name": "Alice", "is_active": True},
                {"id": 2, "name": "Bob", "is_active": False},
                {"id": 3, "name": "Charlie", "is_active": True},
            ]
        }

        result = compiler.execute_compiled(compiled, table_data)

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Charlie"

    def test_execute_with_aggregation(self):
        """Test query with aggregation."""
        compiler = QueryCompiler()

        code = '''
def query_count_by_status(tables):
    users = tables.get("users", [])
    active_count = sum(1 for u in users if u.get("is_active", False))
    inactive_count = sum(1 for u in users if not u.get("is_active", False))

    return [
        {"status": "active", "count": active_count},
        {"status": "inactive", "count": inactive_count}
    ]
'''

        compiled = compiler.compile_query(code)

        table_data = {
            "users": [
                {"id": 1, "is_active": True},
                {"id": 2, "is_active": False},
                {"id": 3, "is_active": True},
                {"id": 4, "is_active": True},
            ]
        }

        result = compiler.execute_compiled(compiled, table_data)

        assert len(result) == 2
        assert result[0]["status"] == "active"
        assert result[0]["count"] == 3
        assert result[1]["status"] == "inactive"
        assert result[1]["count"] == 1

    def test_execute_with_join(self):
        """Test query with join operation."""
        compiler = QueryCompiler()

        code = '''
def query_users_with_orders(tables):
    users = tables.get("users", [])
    orders = tables.get("orders", [])

    result = []
    for user in users:
        user_orders = [o for o in orders if o.get("user_id") == user.get("id")]
        for order in user_orders:
            result.append({
                "user_name": user.get("name"),
                "order_id": order.get("id"),
                "amount": order.get("amount")
            })

    return result
'''

        compiled = compiler.compile_query(code)

        table_data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "orders": [
                {"id": 101, "user_id": 1, "amount": 100},
                {"id": 102, "user_id": 1, "amount": 200},
                {"id": 103, "user_id": 2, "amount": 150},
            ]
        }

        result = compiler.execute_compiled(compiled, table_data)

        assert len(result) == 3
        assert result[0]["user_name"] == "Alice"
        assert result[0]["order_id"] == 101
        assert result[2]["user_name"] == "Bob"

    def test_group_by_utility(self):
        """Test group_by utility function."""
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "A", "value": 30},
            {"category": "B", "value": 40},
        ]

        grouped = QueryCompiler._group_by(data, "category")

        assert len(grouped) == 2
        assert len(grouped["A"]) == 2
        assert len(grouped["B"]) == 2
        assert grouped["A"][0]["value"] == 10
        assert grouped["A"][1]["value"] == 30

    def test_join_tables_utility(self):
        """Test join_tables utility function."""
        left = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        right = [
            {"user_id": 1, "order": "A"},
            {"user_id": 2, "order": "B"},
            {"user_id": 1, "order": "C"},
        ]

        # Inner join
        result = QueryCompiler._join_tables(left, right, "id", "user_id", "inner")
        assert len(result) == 3

        # Left join with no match
        right.append({"user_id": 4, "order": "D"})
        result = QueryCompiler._join_tables(left, right, "id", "user_id", "left")
        assert len(result) == 4  # 3 matches + 1 unmatched Charlie
