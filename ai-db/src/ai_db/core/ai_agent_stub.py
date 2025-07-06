"""Stub AI agent for testing without real API calls."""

import logging

from ai_db.core.ai_agent import ExecutionPlan, FileUpdate
from ai_db.core.models import (
    AIOperation,
    PermissionLevel,
    QueryContext,
)
from ai_db.exceptions import PermissionError

logger = logging.getLogger(__name__)


class AIAgentStub:
    """Stub AI agent that returns predictable responses for testing."""

    def __init__(self) -> None:
        self._max_retries = 3

    async def analyze_query(
        self,
        query: str,
        permissions: PermissionLevel,
        context: QueryContext,
    ) -> AIOperation:
        """Analyze a query and return a predictable operation."""

        # Parse query type from the query string
        query_lower = query.lower().strip()

        if query_lower.startswith('create table'):
            return self._create_table_operation(query, permissions)
        elif query_lower.startswith('select') or 'select' in query_lower:
            return self._select_operation(query, permissions)
        elif query_lower.startswith('insert'):
            return self._insert_operation(query, permissions)
        elif query_lower.startswith('update'):
            return self._update_operation(query, permissions)
        elif query_lower.startswith('delete'):
            return self._delete_operation(query, permissions)
        elif query_lower.startswith('create view'):
            return self._create_view_operation(query, permissions)
        else:
            # Default to select for unknown queries
            return self._select_operation(query, permissions)

    async def generate_execution_plan(
        self,
        query: str,
        operation: AIOperation,
        context: QueryContext,
    ) -> ExecutionPlan:
        """Generate execution plan based on operation type."""

        if operation.operation_type == "select":
            return self._generate_select_plan(query, operation)
        elif operation.operation_type == "create_table":
            return self._generate_create_table_plan(query, operation)
        elif operation.operation_type in ["insert", "update", "delete"]:
            return self._generate_data_modification_plan(query, operation)
        elif operation.operation_type == "create_view":
            return self._generate_create_view_plan(query, operation)
        else:
            return ExecutionPlan(
                file_updates=[],
                python_code=None,
                validation_queries=[],
                error=f"Unknown operation type: {operation.operation_type}"
            )

    async def handle_validation_error(
        self,
        error_message: str,
        operation: AIOperation,
        context: QueryContext,
    ) -> ExecutionPlan | None:
        """Handle validation errors - stub always returns None (no retry)."""
        logger.warning(f"Validation error in stub: {error_message}")
        return None

    def _create_table_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Create table operation."""
        if not self._check_permission(permissions, PermissionLevel.SCHEMA_MODIFY):
            raise PermissionError("schema_modify", permissions.value)

        # Extract table name from query (simple parsing)
        table_name = "users"  # Default for testing
        if "table " in query.lower():
            parts = query.lower().split("table ")
            if len(parts) > 1:
                table_name = parts[1].split()[0].strip("()")

        return AIOperation(
            operation_type="create_table",
            permission_level=PermissionLevel.SCHEMA_MODIFY,
            affected_tables=[table_name],
            requires_python_generation=False,
            validation_required=True,
        )

    def _select_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Select operation."""
        if not self._check_permission(permissions, PermissionLevel.SELECT):
            raise PermissionError("select", permissions.value)

        return AIOperation(
            operation_type="select",
            permission_level=PermissionLevel.SELECT,
            affected_tables=["users"],
            requires_python_generation=True,
            validation_required=False,
        )

    def _insert_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Insert operation."""
        if not self._check_permission(permissions, PermissionLevel.DATA_MODIFY):
            raise PermissionError("data_modify", permissions.value)

        return AIOperation(
            operation_type="insert",
            permission_level=PermissionLevel.DATA_MODIFY,
            affected_tables=["users"],
            requires_python_generation=False,
            validation_required=True,
        )

    def _update_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Update operation."""
        if not self._check_permission(permissions, PermissionLevel.DATA_MODIFY):
            raise PermissionError("data_modify", permissions.value)

        return AIOperation(
            operation_type="update",
            permission_level=PermissionLevel.DATA_MODIFY,
            affected_tables=["users"],
            requires_python_generation=False,
            validation_required=True,
        )

    def _delete_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Delete operation."""
        if not self._check_permission(permissions, PermissionLevel.DATA_MODIFY):
            raise PermissionError("data_modify", permissions.value)

        return AIOperation(
            operation_type="delete",
            permission_level=PermissionLevel.DATA_MODIFY,
            affected_tables=["users"],
            requires_python_generation=False,
            validation_required=True,
        )

    def _create_view_operation(self, query: str, permissions: PermissionLevel) -> AIOperation:
        """Create view operation."""
        if not self._check_permission(permissions, PermissionLevel.VIEW_MODIFY):
            raise PermissionError("view_modify", permissions.value)

        return AIOperation(
            operation_type="create_view",
            permission_level=PermissionLevel.VIEW_MODIFY,
            affected_tables=["users"],
            requires_python_generation=True,
            validation_required=True,
        )

    def _generate_select_plan(self, query: str, operation: AIOperation) -> ExecutionPlan:
        """Generate plan for SELECT queries."""
        # Simple Python code for testing
        python_code = '''
def query_select(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", True)]
'''

        operation.python_code = python_code

        return ExecutionPlan(
            file_updates=[],
            python_code=python_code,
            validation_queries=[],
            error=None
        )

    def _generate_create_table_plan(self, query: str, operation: AIOperation) -> ExecutionPlan:
        """Generate plan for CREATE TABLE."""
        table_name = operation.affected_tables[0] if operation.affected_tables else "users"

        # Simple schema for testing
        schema_content = f'''{{
  "name": "{table_name}",
  "description": "Test table created by stub",
  "columns": [
    {{
      "name": "id",
      "type": "integer",
      "nullable": false,
      "description": "Primary key"
    }},
    {{
      "name": "name",
      "type": "string",
      "nullable": false,
      "description": "Name field"
    }},
    {{
      "name": "email",
      "type": "string",
      "nullable": true,
      "description": "Email field"
    }}
  ],
  "constraints": [
    {{
      "name": "pk_{table_name}",
      "type": "primary_key",
      "columns": ["id"]
    }}
  ]
}}'''

        file_updates = [
            FileUpdate(
                path=f"schemas/{table_name}.schema.yaml",
                content=schema_content,
                operation="create"
            ),
            FileUpdate(
                path=f"tables/{table_name}.yaml",
                content="[]",
                operation="create"
            )
        ]

        operation.file_updates = {
            update.path: update.content for update in file_updates
        }

        return ExecutionPlan(
            file_updates=file_updates,
            python_code=None,
            validation_queries=[],
            error=None
        )

    def _generate_data_modification_plan(self, query: str, operation: AIOperation) -> ExecutionPlan:
        """Generate plan for INSERT/UPDATE/DELETE."""
        table_name = operation.affected_tables[0] if operation.affected_tables else "users"

        # Simple data modification for testing
        if operation.operation_type == "insert":
            table_content = '''[
  {
    "id": 1,
    "name": "Test User",
    "email": "test@example.com"
  }
]'''
        elif operation.operation_type == "update":
            table_content = '''[
  {
    "id": 1,
    "name": "Updated User",
    "email": "updated@example.com"
  }
]'''
        else:  # delete
            table_content = "[]"

        file_updates = [
            FileUpdate(
                path=f"tables/{table_name}.yaml",
                content=table_content,
                operation="update"
            )
        ]

        operation.file_updates = {
            update.path: update.content for update in file_updates
        }

        return ExecutionPlan(
            file_updates=file_updates,
            python_code=None,
            validation_queries=[],
            error=None
        )

    def _generate_create_view_plan(self, query: str, operation: AIOperation) -> ExecutionPlan:
        """Generate plan for CREATE VIEW."""
        view_name = "test_view"

        python_code = '''
def query_test_view(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", True)]
'''

        file_updates = [
            FileUpdate(
                path=f"views/{view_name}.py",
                content=python_code,
                operation="create"
            ),
            FileUpdate(
                path=f"views/{view_name}.meta.yaml",
                content=f'''{{
  "name": "{view_name}",
  "description": "Test view created by stub",
  "dependencies": ["users"]
}}''',
                operation="create"
            )
        ]

        operation.python_code = python_code
        operation.file_updates = {
            update.path: update.content for update in file_updates
        }

        return ExecutionPlan(
            file_updates=file_updates,
            python_code=python_code,
            validation_queries=[],
            error=None
        )

    def _check_permission(self, granted: PermissionLevel, required: PermissionLevel) -> bool:
        """Check if granted permission level is sufficient."""
        permission_hierarchy = {
            PermissionLevel.SELECT: 0,
            PermissionLevel.DATA_MODIFY: 1,
            PermissionLevel.VIEW_MODIFY: 2,
            PermissionLevel.SCHEMA_MODIFY: 3,
        }

        return permission_hierarchy.get(granted, -1) >= permission_hierarchy.get(required, 999)
