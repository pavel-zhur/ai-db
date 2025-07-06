"""Basic usage example for ai-frontend."""

import asyncio
from pathlib import Path

from ai_frontend import AiFrontend, AiFrontendConfig


class MockTransaction:
    """Mock transaction for the example."""

    def __init__(self, path: Path):
        self._path = path
        self._id = "example-transaction"

    @property
    def id(self) -> str:
        return self._id

    @property
    def path(self) -> Path:
        return self._path

    async def write_escalation_required(self) -> None:
        print("Write escalation requested")

    async def operation_complete(self, message: str) -> None:
        print(f"Operation complete: {message}")

    async def operation_failed(self, error_message: str) -> None:
        print(f"Operation failed: {error_message}")


async def main() -> None:
    # Configure ai-frontend
    config = AiFrontendConfig(
        claude_code_path="claude",  # Assumes Claude Code CLI is in PATH
        max_iterations=5,
        timeout_seconds=300,
        api_base_url="http://localhost:8000",
    )

    # Create frontend instance
    frontend = AiFrontend(config)

    # Example AI-DB schema
    schema = {
        "tables": {
            "users": {
                "columns": {
                    "id": {
                        "type": "integer",
                        "primary_key": True,
                        "auto_increment": True,
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "required": True,
                        "unique": True,
                    },
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "user", "guest"],
                        "default": "user",
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "generated": True,
                    },
                }
            },
            "projects": {
                "columns": {
                    "id": {
                        "type": "integer",
                        "primary_key": True,
                        "auto_increment": True,
                    },
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "description": {
                        "type": "string",
                        "nullable": True,
                    },
                    "owner_id": {
                        "type": "integer",
                        "foreign_key": "users.id",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "archived", "deleted"],
                        "default": "active",
                    },
                }
            },
        }
    }

    # Create mock transaction (would come from git-layer in real usage)
    working_dir = Path("/tmp/ai-frontend-test")
    working_dir.mkdir(parents=True, exist_ok=True)
    transaction = MockTransaction(working_dir)

    # Generate frontend
    result = await frontend.generate_frontend(
        request="""
        Create a user management dashboard with:
        - A table showing all users with sorting and pagination
        - Add/Edit user forms with validation
        - Project list for each user
        - Role-based access (admins can edit, others view only)
        - Clean Material-UI design with responsive layout
        """,
        schema=schema,
        transaction=transaction,
        project_name="user-dashboard",
    )

    if result.success:
        print(f"✅ Frontend generated successfully at: {result.output_path}")
        print(f"   Iterations used: {result.iterations_used}")
        print(f"   Compiled: {result.compiled}")
    else:
        print(f"❌ Generation failed: {result.error}")

    # Example of updating an existing frontend
    if result.success:
        update_result = await frontend.update_frontend(
            request="Add a dark mode toggle and user profile avatars",
            schema=schema,
            transaction=transaction,
        )

        if update_result.success:
            print("✅ Frontend updated successfully")
        else:
            print(f"❌ Update failed: {update_result.error}")


if __name__ == "__main__":
    asyncio.run(main())
