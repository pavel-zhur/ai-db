"""Query-related tools for AI-DB."""

from typing import Any, Dict

from ...models.ai_db import PermissionLevel
from .base import AIDBTool


class SchemaModifyTool(AIDBTool):
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

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute schema modification."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required"}

        self._logger.info("Executing schema modification", query=query)

        try:
            # Create transaction for this operation
            async with await self._create_transaction(
                f"Schema modification: {query[:50]}..."
            ) as transaction:
                result = await self._ai_db.execute(
                    query,
                    self.permission_level,
                    transaction,
                )

                return {
                    "success": result.status,
                    "data": result.data,
                    "error": result.error,
                    "data_loss_indicator": (
                        result.data_loss_indicator.value
                        if hasattr(result.data_loss_indicator, "value")
                        else str(result.data_loss_indicator)
                    ),
                    "execution_time": result.execution_time,
                    "compiled_plan": result.compiled_plan,
                }
        except Exception as e:
            self._logger.error("Schema modification failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Schema modification failed: {str(e)}"}


class DataModifyTool(AIDBTool):
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

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data modification."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required"}

        self._logger.info("Executing data modification", query=query)

        try:
            # Create transaction for this operation
            async with await self._create_transaction(
                f"Data modification: {query[:50]}..."
            ) as transaction:
                result = await self._ai_db.execute(
                    query,
                    self.permission_level,
                    transaction,
                )

                return {
                    "success": result.status,
                    "data": result.data,
                    "error": result.error,
                    "data_loss_indicator": (
                        result.data_loss_indicator.value
                        if hasattr(result.data_loss_indicator, "value")
                        else str(result.data_loss_indicator)
                    ),
                    "execution_time": result.execution_time,
                    "compiled_plan": result.compiled_plan,
                }
        except Exception as e:
            self._logger.error("Data modification failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Data modification failed: {str(e)}"}


class SelectTool(AIDBTool):
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

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute select query."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required"}

        self._logger.info("Executing select query", query=query)

        try:
            # Create read-only transaction for this operation
            async with await self._create_transaction(
                f"Select query: {query[:50]}..."
            ) as transaction:
                result = await self._ai_db.execute(
                    query,
                    self.permission_level,
                    transaction,
                )

                return {
                    "success": result.status,
                    "data": result.data,
                    "error": result.error,
                    "data_loss_indicator": (
                        result.data_loss_indicator.value
                        if hasattr(result.data_loss_indicator, "value")
                        else str(result.data_loss_indicator)
                    ),
                    "execution_time": result.execution_time,
                    "compiled_plan": result.compiled_plan,
                }
        except Exception as e:
            self._logger.error("Select query failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Select query failed: {str(e)}"}


class ViewModifyTool(AIDBTool):
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

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute view modification."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required"}

        self._logger.info("Executing view modification", query=query)

        try:
            # Create transaction for this operation
            async with await self._create_transaction(
                f"View modification: {query[:50]}..."
            ) as transaction:
                result = await self._ai_db.execute(
                    query,
                    self.permission_level,
                    transaction,
                )

                return {
                    "success": result.status,
                    "data": result.data,
                    "error": result.error,
                    "data_loss_indicator": (
                        result.data_loss_indicator.value
                        if hasattr(result.data_loss_indicator, "value")
                        else str(result.data_loss_indicator)
                    ),
                    "execution_time": result.execution_time,
                    "compiled_plan": result.compiled_plan,
                }
        except Exception as e:
            self._logger.error("View modification failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"View modification failed: {str(e)}"}


class ExecuteCompiledTool(AIDBTool):
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

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compiled query plan."""
        compiled_plan = params.get("compiled_plan")
        if not compiled_plan:
            return {"success": False, "error": "Compiled plan parameter is required"}

        self._logger.info("Executing compiled query plan")

        try:
            # Create read-only transaction for this operation
            async with await self._create_transaction("Execute compiled query") as transaction:
                result = await self._ai_db.execute_compiled(
                    compiled_plan,
                    transaction,
                )

                return {
                    "success": result.status,
                    "data": result.data,
                    "error": result.error,
                    "data_loss_indicator": (
                        result.data_loss_indicator.value
                        if hasattr(result.data_loss_indicator, "value")
                        else str(result.data_loss_indicator)
                    ),
                    "execution_time": result.execution_time,
                }
        except Exception as e:
            self._logger.error("Compiled query execution failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Compiled query execution failed: {str(e)}"}


class CompileQueryTool(AIDBTool):
    """Tool for compiling queries for future reuse."""

    @property
    def name(self) -> str:
        return "compile_query"

    @property
    def description(self) -> str:
        return "Compile a query to a reusable plan for performance optimization"

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.SELECT

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compile a query."""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required"}

        self._logger.info("Compiling query", query=query)

        try:
            # Create read-only transaction for this operation
            async with await self._create_transaction(
                f"Compile query: {query[:50]}..."
            ) as transaction:
                compiled_plan = await self._ai_db.compile_query(query, transaction)

                return {
                    "success": True,
                    "compiled_plan": compiled_plan,
                    "query": query,
                }
        except Exception as e:
            self._logger.error("Query compilation failed", error=str(e), exc_info=True)
            return {"success": False, "error": f"Query compilation failed: {str(e)}"}
