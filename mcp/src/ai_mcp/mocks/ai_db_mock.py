"""Mock implementation of AI-DB for testing."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_shared.protocols import TransactionProtocol

from ..models.ai_db import DataLossIndicator, PermissionLevel


class MockQueryResult:
    """Mock query result that matches ai-db interface."""

    def __init__(
        self,
        status: bool = True,
        data: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
        execution_time: float = 0.1,
        compiled_plan: Optional[str] = None,
        data_loss_indicator: DataLossIndicator = DataLossIndicator.NONE,
    ):
        self.status = status
        self.data = data
        self.error = error
        self.execution_time = execution_time
        self.compiled_plan = compiled_plan
        self.data_loss_indicator = data_loss_indicator


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
        self._data: Dict[str, List[Dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ]
        }

    async def execute(
        self,
        query: str,
        permissions: PermissionLevel,
        transaction: TransactionProtocol,
        context: Optional[Dict[str, Any]] = None,
    ) -> MockQueryResult:
        """Execute a mock query."""
        print(f"Mock AI-DB: Executing query '{query}' with permission {permissions}")

        # Simple mock logic based on query content
        query_lower = query.lower()

        if "select" in query_lower or "show" in query_lower or "get" in query_lower:
            return MockQueryResult(
                status=True,
                data=self._data.get("users", []),
                execution_time=0.05,
                compiled_plan="mock_compiled_select_plan",
            )
        elif "create" in query_lower or "add" in query_lower:
            return MockQueryResult(
                status=True,
                data_loss_indicator=DataLossIndicator.NONE,
                execution_time=0.15,
            )
        elif "drop" in query_lower or "delete" in query_lower:
            return MockQueryResult(
                status=True,
                data_loss_indicator=DataLossIndicator.YES,
                execution_time=0.1,
            )
        elif "update" in query_lower or "modify" in query_lower:
            return MockQueryResult(
                status=True,
                data_loss_indicator=DataLossIndicator.PROBABLE,
                execution_time=0.12,
            )
        else:
            return MockQueryResult(
                status=True,
                execution_time=0.08,
            )

    async def compile_query(
        self,
        query: str,
        transaction: TransactionProtocol,
    ) -> str:
        """Compile a query to a reusable plan."""
        print(f"Mock AI-DB: Compiling query '{query}'")
        return f"mock_compiled_plan_for_{hash(query) % 1000}"

    async def execute_compiled(
        self,
        compiled_plan: str,
        transaction: TransactionProtocol,
    ) -> MockQueryResult:
        """Execute a compiled query plan."""
        print(f"Mock AI-DB: Executing compiled plan '{compiled_plan}'")
        return MockQueryResult(
            status=True,
            data=[{"result": "compiled_execution", "plan": compiled_plan}],
            execution_time=0.02,  # Compiled queries are faster
        )

    async def get_schema(self, transaction: TransactionProtocol) -> Dict[str, Any]:
        """Get current schema."""
        print("Mock AI-DB: Getting schema")
        return self._schema

    async def init_from_folder(
        self,
        transaction: TransactionProtocol,
        source_folder: Path,
    ) -> None:
        """Initialize database from existing folder."""
        print(f"Mock AI-DB: Initializing from folder {source_folder}")
        # Mock initialization - just add some test data
        self._data["imported"] = [{"id": 1, "imported_from": str(source_folder)}]
