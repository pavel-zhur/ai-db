"""Query-related tools for AI-DB."""

from typing import Any
import structlog

from .base import AIDBTool
from ...models.ai_db import (
    PermissionLevel,
    QueryRequest,
    QueryResponse,
    DataLossIndicator,
)


class SchemaModifyTool(AIDBTool[QueryRequest, QueryResponse]):
    """Tool for modifying database schema."""
    
    @property
    def name(self) -> str:
        return "schema_modify"
    
    @property
    def description(self) -> str:
        return "Modify table schemas, manage relationships, and constraints"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SCHEMA_MODIFY
    
    async def execute(self, params: QueryRequest) -> QueryResponse:
        """Execute schema modification."""
        self._logger.info(
            "Executing schema modification",
            query=params.query,
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_db.execute(
                params.query,
                self.permission_level,
                transaction_context,
            )
            
            return QueryResponse(
                status=result.status,
                data=result.data,
                schema=result.schema,
                data_loss_indicator=result.data_loss_indicator,
                ai_comment=result.ai_comment,
                compiled_plan=result.compiled_plan,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("Schema modification failed", error=str(e))
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="Schema modification failed",
                error=str(e),
            )


class DataModifyTool(AIDBTool[QueryRequest, QueryResponse]):
    """Tool for modifying data."""
    
    @property
    def name(self) -> str:
        return "data_modify"
    
    @property
    def description(self) -> str:
        return "Insert, update, and delete data operations"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.DATA_MODIFY
    
    async def execute(self, params: QueryRequest) -> QueryResponse:
        """Execute data modification."""
        self._logger.info(
            "Executing data modification",
            query=params.query,
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_db.execute(
                params.query,
                self.permission_level,
                transaction_context,
            )
            
            return QueryResponse(
                status=result.status,
                data=result.data,
                schema=result.schema,
                data_loss_indicator=result.data_loss_indicator,
                ai_comment=result.ai_comment,
                compiled_plan=result.compiled_plan,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("Data modification failed", error=str(e))
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="Data modification failed",
                error=str(e),
            )


class SelectTool(AIDBTool[QueryRequest, QueryResponse]):
    """Tool for selecting data."""
    
    @property
    def name(self) -> str:
        return "select"
    
    @property
    def description(self) -> str:
        return "Execute complex queries with joins and aggregations"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SELECT
    
    async def execute(self, params: QueryRequest) -> QueryResponse:
        """Execute select query."""
        self._logger.info(
            "Executing select query",
            query=params.query,
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_db.execute(
                params.query,
                self.permission_level,
                transaction_context,
            )
            
            return QueryResponse(
                status=result.status,
                data=result.data,
                schema=result.schema,
                data_loss_indicator=result.data_loss_indicator,
                ai_comment=result.ai_comment,
                compiled_plan=result.compiled_plan,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("Select query failed", error=str(e))
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="Select query failed",
                error=str(e),
            )


class ViewModifyTool(AIDBTool[QueryRequest, QueryResponse]):
    """Tool for modifying views."""
    
    @property
    def name(self) -> str:
        return "view_modify"
    
    @property
    def description(self) -> str:
        return "Create and modify database views"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.VIEW_MODIFY
    
    async def execute(self, params: QueryRequest) -> QueryResponse:
        """Execute view modification."""
        self._logger.info(
            "Executing view modification",
            query=params.query,
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_db.execute(
                params.query,
                self.permission_level,
                transaction_context,
            )
            
            return QueryResponse(
                status=result.status,
                data=result.data,
                schema=result.schema,
                data_loss_indicator=result.data_loss_indicator,
                ai_comment=result.ai_comment,
                compiled_plan=result.compiled_plan,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("View modification failed", error=str(e))
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="View modification failed",
                error=str(e),
            )


class ExecuteCompiledTool(AIDBTool[QueryRequest, QueryResponse]):
    """Tool for executing pre-compiled query plans."""
    
    @property
    def name(self) -> str:
        return "execute_compiled"
    
    @property
    def description(self) -> str:
        return "Execute pre-compiled query plans for optimal performance"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SELECT
    
    async def execute(self, params: QueryRequest) -> QueryResponse:
        """Execute compiled query plan."""
        if not params.query:  # Using query field to pass compiled plan
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="No compiled plan provided",
                error="Compiled plan is required",
            )
        
        self._logger.info(
            "Executing compiled query plan",
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_db.execute_compiled(
                params.query,  # Contains the compiled plan
                transaction_context,
            )
            
            return QueryResponse(
                status=result.status,
                data=result.data,
                schema=result.schema,
                data_loss_indicator=result.data_loss_indicator,
                ai_comment=result.ai_comment,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("Compiled query execution failed", error=str(e))
            return QueryResponse(
                status="error",
                data_loss_indicator=DataLossIndicator.NONE,
                ai_comment="Compiled query execution failed",
                error=str(e),
            )