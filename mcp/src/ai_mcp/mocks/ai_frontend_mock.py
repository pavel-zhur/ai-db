"""Mock implementation of AI-Frontend for testing."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_shared.protocols import TransactionProtocol


class MockGenerationResult:
    """Mock generation result that matches ai-frontend interface."""

    def __init__(
        self,
        success: bool = True,
        output_path: Optional[Path] = None,
        error: Optional[str] = None,
        compiled: bool = True,
        iterations_used: int = 1,
    ):
        self.success = success
        self.output_path = output_path
        self.error = error
        self.compiled = compiled
        self.iterations_used = iterations_used


class MockAIFrontend:
    """Mock AI-Frontend implementation for testing."""

    def __init__(self) -> None:
        """Initialize mock AI-Frontend."""
        self._schema: Optional[Dict[str, Any]] = None
        self._generated_files: List[str] = []

    async def generate_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction: TransactionProtocol,
        project_name: str,
    ) -> MockGenerationResult:
        """Generate mock frontend components."""
        print(f"Mock AI-Frontend: Generating frontend '{project_name}' with request '{request}'")

        # Store schema for later retrieval
        self._schema = schema

        # Mock different outcomes based on request content
        if "error" in request.lower():
            return MockGenerationResult(
                success=False,
                error="Mock generation error for testing",
            )

        mock_output_path = transaction.path / "frontend" / project_name

        # Simulate different component types
        if "dashboard" in request.lower():
            self._generated_files = [
                "src/components/Dashboard.tsx",
                "src/components/DashboardWidget.tsx",
                "src/services/dashboardApi.ts",
            ]
        elif "form" in request.lower():
            self._generated_files = [
                "src/components/UserForm.tsx",
                "src/components/FormField.tsx",
            ]
        else:
            self._generated_files = [
                "src/App.tsx",
                "src/components/MainComponent.tsx",
                "src/types/api.ts",
            ]

        return MockGenerationResult(
            success=True,
            output_path=mock_output_path,
            compiled=True,
            iterations_used=1,
        )

    async def update_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction: TransactionProtocol,
    ) -> MockGenerationResult:
        """Update mock frontend components."""
        print(f"Mock AI-Frontend: Updating frontend with request '{request}'")

        # Update stored schema
        self._schema = schema

        if "error" in request.lower():
            return MockGenerationResult(
                success=False,
                error="Mock update error for testing",
            )

        mock_output_path = transaction.path / "frontend"

        # Add some new files to the existing ones
        new_files = ["src/components/UpdatedComponent.tsx"]
        self._generated_files.extend(new_files)

        return MockGenerationResult(
            success=True,
            output_path=mock_output_path,
            compiled=True,
            iterations_used=2,
        )

    async def get_schema(self, transaction: TransactionProtocol) -> Optional[Dict[str, Any]]:
        """Get the current frontend schema."""
        print("Mock AI-Frontend: Getting schema")
        return self._schema

    async def init_from_folder(
        self,
        source_path: Path,
        transaction: TransactionProtocol,
    ) -> None:
        """Initialize frontend from a seed folder."""
        print(f"Mock AI-Frontend: Initializing from folder {source_path}")

        # Mock initialization - set some default schema and files
        self._schema = {
            "tables": {
                "imported_data": {
                    "columns": {
                        "id": {"type": "integer", "primary_key": True},
                        "name": {"type": "string"},
                    }
                }
            }
        }
        self._generated_files = [
            "src/App.tsx",
            "src/components/ImportedComponent.tsx",
        ]
