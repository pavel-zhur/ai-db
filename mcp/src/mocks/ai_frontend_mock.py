"""Mock implementation of AI-Frontend for testing."""

from typing import Any, Optional
from ..protocols import AIFrontendProtocol, AIFrontendResult


class MockAIFrontend:
    """Mock AI-Frontend implementation for testing."""
    
    def __init__(self) -> None:
        """Initialize mock AI-Frontend."""
        self._components = [
            {"name": "UserList", "path": "/components/UserList.tsx"},
            {"name": "UserForm", "path": "/components/UserForm.tsx"},
        ]
    
    async def generate(
        self,
        request: str,
        transaction_context: Optional[Any] = None,
    ) -> AIFrontendResult:
        """Generate mock frontend components."""
        # Simple mock logic
        if "dashboard" in request.lower():
            return AIFrontendResult(
                status="success",
                generated_files=[
                    "/components/Dashboard.tsx",
                    "/components/DashboardWidget.tsx",
                ],
                ai_comment="Generated dashboard components",
            )
        elif "form" in request.lower():
            return AIFrontendResult(
                status="success",
                generated_files=["/components/UserForm.tsx"],
                ai_comment="Generated form component",
            )
        else:
            return AIFrontendResult(
                status="success",
                generated_files=["/components/NewComponent.tsx"],
                ai_comment="Generated component based on request",
            )
    
    async def get_frontend_info(self) -> dict[str, Any]:
        """Get frontend information."""
        return {
            "components": self._components,
            "semantic_docs": {
                "UserList": "Component for displaying list of users",
                "UserForm": "Form component for user data entry",
            }
        }