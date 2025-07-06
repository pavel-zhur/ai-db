"""Unit tests for storage layer."""


import pytest
from ai_shared.protocols import TransactionProtocol

from ai_db.core.models import Column, Constraint, ConstraintType, Table
from ai_db.storage import SchemaStore, ViewStore, YAMLStore


class TestYAMLStore:
    """Test YAML storage operations."""

    @pytest.mark.asyncio
    async def test_read_empty_table(self, transaction_context: TransactionProtocol):
        """Test reading a non-existent table returns empty list."""
        store = YAMLStore(transaction_context)
        data = await store.read_table("nonexistent")
        assert data == []

    @pytest.mark.asyncio
    async def test_write_and_read_table(self, transaction_context: TransactionProtocol, sample_data):
        """Test writing and reading table data."""
        store = YAMLStore(transaction_context)

        # Write data
        await store.write_table("users", sample_data)

        # Read back
        data = await store.read_table("users")
        assert len(data) == 3
        assert data[0]["username"] == "alice"
        assert data[1]["username"] == "bob"
        assert data[2]["username"] == "charlie"

    @pytest.mark.asyncio
    async def test_list_tables(self, transaction_context: TransactionProtocol):
        """Test listing tables."""
        store = YAMLStore(transaction_context)

        # Initially empty
        tables = await store.list_tables()
        assert tables == []

        # Write some tables
        await store.write_table("users", [])
        await store.write_table("products", [])

        # List again
        tables = await store.list_tables()
        assert sorted(tables) == ["products", "users"]

    @pytest.mark.asyncio
    async def test_write_escalation(self, transaction_context: TransactionProtocol):
        """Test write escalation."""
        store = YAMLStore(transaction_context)

        # Write should trigger escalation
        await store.write_table("test", [{"id": 1}])

        # Verify write_escalation_required was called
        transaction_context.write_escalation_required.assert_called_once()
        # Verify operation_complete was called
        transaction_context.operation_complete.assert_called()


class TestSchemaStore:
    """Test schema storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_table_schema(
        self,
        transaction_context: TransactionProtocol,
        sample_schema
    ):
        """Test saving and loading table schema."""
        store = SchemaStore(transaction_context)

        # Create table from schema
        table = Table(
            name=sample_schema["name"],
            description=sample_schema["description"],
            columns=[
                Column(**col) for col in sample_schema["columns"]
            ],
            constraints=[
                Constraint(
                    name=c["name"],
                    type=ConstraintType(c["type"]),
                    columns=c["columns"],
                    definition=c.get("definition")
                ) for c in sample_schema["constraints"]
            ]
        )

        # Save schema
        await store.save_table_schema(table)

        # Load schema
        schema = await store.load_schema()
        assert "users" in schema.tables
        loaded_table = schema.tables["users"]

        assert loaded_table.name == "users"
        assert len(loaded_table.columns) == 5
        assert len(loaded_table.constraints) == 4
        assert loaded_table.columns[0].name == "id"
        assert loaded_table.columns[0].nullable is False

    @pytest.mark.asyncio
    async def test_semantic_documentation(self, transaction_context: TransactionProtocol):
        """Test saving and loading semantic documentation."""
        store = SchemaStore(transaction_context)

        docs = {
            "users": "Table containing user account information",
            "users.email": "User's primary email address for communication"
        }

        await store.save_semantic_documentation(docs)

        schema = await store.load_schema()
        assert schema.semantic_documentation == docs


class TestViewStore:
    """Test view storage operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_view(self, transaction_context: TransactionProtocol):
        """Test saving and loading views."""
        store = ViewStore(transaction_context)

        python_code = '''
def query_active_users(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", False)]
'''

        metadata = {
            "description": "Returns all active users",
            "tables": ["users"],
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Save view
        await store.save_view("active_users", python_code, metadata)

        # Load view
        loaded_code, loaded_meta = await store.load_view("active_users")

        assert loaded_code == python_code
        assert loaded_meta == metadata

    @pytest.mark.asyncio
    async def test_list_views(self, transaction_context: TransactionProtocol):
        """Test listing views."""
        store = ViewStore(transaction_context)

        # Initially empty
        views = await store.list_views()
        assert views == []

        # Save some views
        await store.save_view("view1", "code1", {})
        await store.save_view("view2", "code2", {})

        # List again
        views = await store.list_views()
        assert sorted(views) == ["view1", "view2"]
