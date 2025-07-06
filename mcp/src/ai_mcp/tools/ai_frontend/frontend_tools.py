"""Frontend generation tools for AI-Frontend."""

from pathlib import Path
from typing import Any, Dict

from .base import AIFrontendTool


class GenerateFrontendTool(AIFrontendTool):
    """Tool for generating new frontends."""

    @property
    def name(self) -> str:
        return "generate_frontend"

    @property
    def description(self) -> str:
        return (
            "Generate a complete React frontend from natural language request and database schema"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a frontend."""
        request = params.get("request", "")
        schema = params.get("schema", {})
        project_name = params.get("project_name", "")

        if not request:
            return {"success": False, "error": "Request parameter is required"}
        if not schema:
            return {"success": False, "error": "Schema parameter is required"}
        if not project_name:
            return {"success": False, "error": "Project name parameter is required"}

        self._logger.info("Generating frontend", request=request, project_name=project_name)

        try:
            # Create transaction for this operation
            async with self._create_transaction(
                f"Generate frontend: {project_name}"
            ) as transaction:
                result = await self._ai_frontend.generate_frontend(
                    request,
                    schema,
                    transaction,
                    project_name,
                )

                return {
                    "success": result.success,
                    "output_path": str(result.output_path) if result.output_path else None,
                    "error": result.error,
                    "compiled": result.compiled,
                    "iterations_used": result.iterations_used,
                }
        except Exception as e:
            self._logger.error("Frontend generation failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Frontend generation failed: {str(e)}"}


class UpdateFrontendTool(AIFrontendTool):
    """Tool for updating existing frontends."""

    @property
    def name(self) -> str:
        return "update_frontend"

    @property
    def description(self) -> str:
        return "Update an existing frontend based on natural language request and updated schema"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a frontend."""
        request = params.get("request", "")
        schema = params.get("schema", {})

        if not request:
            return {"success": False, "error": "Request parameter is required"}
        if not schema:
            return {"success": False, "error": "Schema parameter is required"}

        self._logger.info("Updating frontend", request=request)

        try:
            # Create transaction for this operation
            async with self._create_transaction(
                f"Update frontend: {request[:50]}..."
            ) as transaction:
                result = await self._ai_frontend.update_frontend(
                    request,
                    schema,
                    transaction,
                )

                return {
                    "success": result.success,
                    "output_path": str(result.output_path) if result.output_path else None,
                    "error": result.error,
                    "compiled": result.compiled,
                    "iterations_used": result.iterations_used,
                }
        except Exception as e:
            self._logger.error("Frontend update failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Frontend update failed: {str(e)}"}


class GetFrontendSchemaTool(AIFrontendTool):
    """Tool for getting frontend schema."""

    @property
    def name(self) -> str:
        return "get_frontend_schema"

    @property
    def description(self) -> str:
        return "Get the current database schema stored with the frontend"

    @property
    def destructive_hint(self) -> bool:
        """This tool only reads data."""
        return False

    @property
    def read_only_hint(self) -> bool:
        """This tool only reads data."""
        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get frontend schema."""
        self._logger.info("Getting frontend schema")

        try:
            # Create read-only transaction for this operation
            async with self._create_transaction("Get frontend schema") as transaction:
                schema = await self._ai_frontend.get_schema(transaction)

                return {
                    "success": True,
                    "schema": schema,
                }
        except Exception as e:
            self._logger.error("Failed to get frontend schema", error=str(e), exc_info=True)
            return {"success": False, "error": f"Failed to get frontend schema: {str(e)}"}


class InitFrontendFromFolderTool(AIFrontendTool):
    """Tool for initializing frontend from existing folder."""

    @property
    def name(self) -> str:
        return "init_frontend_from_folder"

    @property
    def description(self) -> str:
        return "Initialize frontend from existing seed files folder"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize frontend from folder."""
        source_path = params.get("source_path")
        if not source_path:
            return {"success": False, "error": "Source path parameter is required"}

        self._logger.info("Initializing frontend from folder", source_path=source_path)

        try:
            # Create transaction for this operation
            async with self._create_transaction(
                f"Initialize frontend from: {source_path}"
            ) as transaction:
                await self._ai_frontend.init_from_folder(
                    Path(source_path),
                    transaction,
                )

                return {"success": True, "message": f"Frontend initialized from {source_path}"}
        except Exception as e:
            self._logger.error(
                "Failed to initialize frontend from folder", error=str(e), exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to initialize frontend from folder: {str(e)}",
            }
