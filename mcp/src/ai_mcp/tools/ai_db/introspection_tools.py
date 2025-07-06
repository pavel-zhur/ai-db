"""Introspection tools for AI-DB."""

from typing import Any, Dict

from ...models.ai_db import PermissionLevel
from .base import AIDBTool


class GetSchemaTool(AIDBTool):
    """Tool for getting database schema."""

    @property
    def name(self) -> str:
        return "get_schema"

    @property
    def description(self) -> str:
        return "Get current database schema with semantic descriptions"

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SELECT

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get database schema."""
        include_semantic_docs = params.get("include_semantic_docs", True)

        self._logger.info(
            "Getting database schema",
            include_semantic_docs=include_semantic_docs,
        )

        try:
            # Create read-only transaction for this operation
            async with await self._create_transaction("Get schema") as transaction:
                schema = await self._ai_db.get_schema(transaction)

                return {
                    "success": True,
                    "schema": schema,
                }
        except Exception as e:
            self._logger.error("Failed to get schema", error=str(e), exc_info=True)
            return {"success": False, "error": f"Failed to get schema: {str(e)}"}


class InitFromFolderTool(AIDBTool):
    """Tool for initializing database from existing folder."""

    @property
    def name(self) -> str:
        return "init_from_folder"

    @property
    def description(self) -> str:
        return "Initialize database from existing seed data folder"

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SCHEMA_MODIFY

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize database from folder."""
        source_folder = params.get("source_folder")
        if not source_folder:
            return {"success": False, "error": "Source folder parameter is required"}

        self._logger.info("Initializing database from folder", source_folder=source_folder)

        try:
            from pathlib import Path

            # Create transaction for this operation
            async with await self._create_transaction(
                f"Initialize from folder: {source_folder}"
            ) as transaction:
                await self._ai_db.init_from_folder(transaction, Path(source_folder))

                return {"success": True, "message": f"Database initialized from {source_folder}"}
        except Exception as e:
            self._logger.error("Failed to initialize from folder", error=str(e), exc_info=True)
            return {"success": False, "error": f"Failed to initialize from folder: {str(e)}"}
