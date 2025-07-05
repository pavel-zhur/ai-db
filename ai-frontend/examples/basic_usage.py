"""Basic usage example for ai-frontend."""

import asyncio
from pathlib import Path

from ai_frontend import AiFrontend, AiFrontendConfig
from ai_frontend.core import TransactionContext


async def main():
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
    
    # Create transaction context (would come from git-layer in real usage)
    transaction_context = TransactionContext(
        transaction_id="test-transaction-1",
        working_directory=Path("/tmp/ai-frontend-test"),
        commit_message_callback=lambda msg: print(f"Commit message: {msg}"),
    )
    
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
        transaction_context=transaction_context,
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
            transaction_context=transaction_context,
        )
        
        if update_result.success:
            print(f"✅ Frontend updated successfully")
        else:
            print(f"❌ Update failed: {update_result.error}")


if __name__ == "__main__":
    asyncio.run(main())