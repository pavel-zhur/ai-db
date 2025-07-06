"""Introspection tools for AI-DB."""

from typing import Any
import structlog

from .base import AIDBTool
from ...models.ai_db import (
    PermissionLevel,
    SchemaRequest,
    SchemaResponse,
)


class GetSchemaTool(AIDBTool[SchemaRequest, SchemaResponse]):
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
    
    async def execute(self, params: SchemaRequest) -> SchemaResponse:
        """Get database schema."""
        self._logger.info(
            "Getting database schema",
            include_semantic_docs=params.include_semantic_docs,
        )
        
        try:
            result = await self._ai_db.get_schema(params.include_semantic_docs)
            
            return SchemaResponse(
                schema=result["schema"],
                semantic_docs=result.get("semantic_docs") if params.include_semantic_docs else None,
            )
        except Exception as e:
            self._logger.error("Failed to get schema", error=str(e))
            return SchemaResponse(
                schema={},
                error=str(e),
            )