"""Mock implementation of AI-DB for testing."""

from typing import Any, Optional
from ..models.ai_db import PermissionLevel, DataLossIndicator
from ..protocols import AIDBProtocol, AIDBQueryResult


class MockAIDB:
    """Mock AI-DB implementation for testing."""
    
    def __init__(self) -> None:
        """Initialize mock AI-DB."""
        self._schema = {
            "tables": {
                "users": {
                    "columns": {
                        "id": {"type": "integer", "primary_key": True},
                        "name": {"type": "string", "nullable": False},
                        "email": {"type": "string", "nullable": False},
                    }
                }
            }
        }
        self._data: dict[str, list[dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ]
        }
    
    async def execute(
        self,
        query: str,
        permission_level: PermissionLevel,
        transaction_context: Optional[Any] = None,
    ) -> AIDBQueryResult:
        """Execute a mock query."""
        # Simple mock logic
        if "select" in query.lower():
            return AIDBQueryResult(
                status="success",
                data=self._data.get("users", []),
                schema={"columns": ["id", "name", "email"]},
                ai_comment="Selected all users",
            )
        elif "create table" in query.lower():
            return AIDBQueryResult(
                status="success",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="Created new table",
            )
        elif "drop" in query.lower():
            return AIDBQueryResult(
                status="success",
                data_loss_indicator=DataLossIndicator.YES,
                ai_comment="Dropped table/data",
            )
        else:
            return AIDBQueryResult(
                status="success",
                ai_comment="Operation completed",
            )
    
    async def execute_compiled(
        self,
        compiled_plan: str,
        transaction_context: Optional[Any] = None,
    ) -> AIDBQueryResult:
        """Execute a compiled query plan."""
        return AIDBQueryResult(
            status="success",
            data=[{"result": "compiled"}],
            schema={"columns": ["result"]},
            ai_comment="Executed compiled plan",
        )
    
    async def get_schema(self, include_semantic_docs: bool = True) -> dict[str, Any]:
        """Get current schema."""
        result = {"schema": self._schema}
        if include_semantic_docs:
            result["semantic_docs"] = {
                "tables": {
                    "users": "Table storing user information"
                }
            }
        return result