"""Core service for AI-Hub."""

import asyncio
import logging
import os
from typing import Awaitable, TypeVar

import git_layer
from ai_db import AIDB
from ai_db.core.models import PermissionLevel as AIDBPermissionLevel

from .config import Config
from .models import DataLossIndicator, PermissionLevel, QueryResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AIHubService:
    """Core service for AI-Hub operations."""

    def __init__(self, config: Config) -> None:
        """Initialize the service with configuration."""
        self._config = config
        self._setup_aidb_environment()
        self._aidb = AIDB()

    def _setup_aidb_environment(self) -> None:
        """Set up AI-DB environment variables from ai-hub config."""
        # Set AI-DB environment variables that AI-DB will read
        if self._config.ai_db_api_key:
            os.environ["AI_DB_API_KEY"] = self._config.ai_db_api_key
        if self._config.ai_db_api_base:
            os.environ["AI_DB_API_BASE"] = self._config.ai_db_api_base
        if self._config.ai_db_model:
            os.environ["AI_DB_MODEL"] = self._config.ai_db_model

        os.environ["AI_DB_TEMPERATURE"] = str(self._config.ai_db_temperature)
        os.environ["AI_DB_TIMEOUT_SECONDS"] = str(self._config.ai_db_timeout_seconds)
        os.environ["AI_DB_MAX_RETRIES"] = str(self._config.ai_db_max_retries)

    @property
    def aidb(self) -> AIDB:
        """Get AI-DB instance."""
        return self._aidb

    def _convert_permission_level(self, permission: PermissionLevel) -> AIDBPermissionLevel:
        """Convert API permission level to AI-DB permission level."""
        return AIDBPermissionLevel(permission.value)

    def _convert_data_loss_indicator(self, indicator: object) -> DataLossIndicator:
        """Convert AI-DB data loss indicator to API model."""
        if hasattr(indicator, "value"):
            return DataLossIndicator(indicator.value)
        return DataLossIndicator.NONE

    async def _execute_with_progress(self, operation_coro: Awaitable[T], operation_desc: str) -> T:
        """Execute operation with progress feedback."""
        progress_task = None

        try:
            # Start progress feedback task
            progress_task = asyncio.create_task(self._progress_feedback(operation_desc))

            # Execute the operation
            result = await operation_coro

            return result

        finally:
            # Cancel progress feedback
            if progress_task:
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass

    async def _progress_feedback(self, operation_desc: str) -> None:
        """Provide periodic progress feedback."""
        while True:
            await asyncio.sleep(self._config.progress_feedback_interval)
            logger.info(f"Still working on: {operation_desc}...")

    async def execute_query(self, query: str, permissions: PermissionLevel) -> QueryResponse:
        """Execute a query operation."""
        operation_desc = f"query execution: {query[:50]}..."

        async def _execute() -> QueryResponse:
            async with await git_layer.begin(
                self._config.git_repo_path, message=f"Execute query: {query[:50]}..."
            ) as transaction:
                try:
                    result = await self.aidb.execute(
                        query=query,
                        permissions=self._convert_permission_level(permissions),
                        transaction=transaction,
                    )

                    await transaction.operation_complete("Query executed successfully")

                    return QueryResponse(
                        success=result.status,
                        data=result.data,
                        result_schema=result.schema,
                        data_loss_indicator=self._convert_data_loss_indicator(
                            result.data_loss_indicator
                        ),
                        ai_comment=result.ai_comment,
                        compiled_plan=result.compiled_plan,
                        transaction_id=result.transaction_id,
                        error=result.error,
                        error_details=None,
                        execution_time=result.execution_time,
                    )

                except Exception as e:
                    await transaction.operation_failed(f"Query failed: {str(e)}")
                    raise

        return await self._execute_with_progress(_execute(), operation_desc)

    async def execute_view(
        self, view_name: str, parameters: dict[str, object] | None
    ) -> QueryResponse:
        """Execute a view query."""
        operation_desc = f"view execution: {view_name}"

        async def _execute() -> QueryResponse:
            async with await git_layer.begin(
                self._config.git_repo_path, message=f"Execute view: {view_name}"
            ) as transaction:
                try:
                    # Construct view query with parameters
                    if parameters:
                        param_str = ", ".join(f"{k}={v}" for k, v in parameters.items())
                        query = f"SELECT * FROM {view_name} WHERE {param_str}"
                    else:
                        query = f"SELECT * FROM {view_name}"

                    result = await self.aidb.execute(
                        query=query,
                        permissions=self._convert_permission_level(PermissionLevel.SELECT),
                        transaction=transaction,
                    )

                    await transaction.operation_complete(f"View {view_name} executed successfully")

                    return QueryResponse(
                        success=result.status,
                        data=result.data,
                        result_schema=result.schema,
                        data_loss_indicator=self._convert_data_loss_indicator(
                            result.data_loss_indicator
                        ),
                        ai_comment=result.ai_comment,
                        compiled_plan=result.compiled_plan,
                        transaction_id=result.transaction_id,
                        error=result.error,
                        error_details=None,
                        execution_time=result.execution_time,
                    )

                except Exception as e:
                    await transaction.operation_failed(f"View execution failed: {str(e)}")
                    raise

        return await self._execute_with_progress(_execute(), operation_desc)

    async def execute_data_modification(
        self, operation: str, permissions: PermissionLevel
    ) -> QueryResponse:
        """Execute a data modification operation."""
        operation_desc = f"data modification: {operation[:50]}..."

        async def _execute() -> QueryResponse:
            async with await git_layer.begin(
                self._config.git_repo_path, message=f"Data modification: {operation[:50]}..."
            ) as transaction:
                try:
                    # Signal write escalation since we're modifying data
                    await transaction.write_escalation_required()

                    result = await self.aidb.execute(
                        query=operation,
                        permissions=self._convert_permission_level(permissions),
                        transaction=transaction,
                    )

                    await transaction.operation_complete("Data modification completed successfully")

                    return QueryResponse(
                        success=result.status,
                        data=result.data,
                        result_schema=result.schema,
                        data_loss_indicator=self._convert_data_loss_indicator(
                            result.data_loss_indicator
                        ),
                        ai_comment=result.ai_comment,
                        compiled_plan=result.compiled_plan,
                        transaction_id=result.transaction_id,
                        error=result.error,
                        error_details=None,
                        execution_time=result.execution_time,
                    )

                except Exception as e:
                    await transaction.operation_failed(f"Data modification failed: {str(e)}")
                    raise

        return await self._execute_with_progress(_execute(), operation_desc)
