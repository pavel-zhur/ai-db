"""Core AI-DB engine implementation."""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from dependency_injector import containers, providers

from ai_db.core.models import (
    PermissionLevel,
    QueryResult,
    QueryContext,
    DataLossIndicator,
    AIOperation,
)
from ai_shared.protocols import TransactionProtocol
from ai_db.core.ai_agent import AIAgent
from ai_db.core.ai_agent_stub import AIAgentStub
from ai_db.config import get_config
from ai_db.core.query_compiler import QueryCompiler
from ai_db.storage import YAMLStore, SchemaStore, ViewStore
from ai_db.validation import DataValidator, ConstraintChecker, SafeExecutor
from ai_db.transaction import TransactionManager
from ai_db.exceptions import AIDBError, ValidationError, PermissionError

logger = logging.getLogger(__name__)


class DIContainer(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    config = providers.Configuration()
    
    # Core components
    ai_agent = providers.Singleton(AIAgent)
    query_compiler = providers.Singleton(QueryCompiler)
    safe_executor = providers.Singleton(SafeExecutor)
    data_validator = providers.Singleton(DataValidator)
    
    # Per-transaction components
    transaction_context = providers.Dependency()  # Will be TransactionProtocol
    
    transaction_manager = providers.Factory(
        TransactionManager,
        transaction_context=transaction_context,
    )
    
    yaml_store = providers.Factory(
        YAMLStore,
        transaction_context=transaction_context,
    )
    
    schema_store = providers.Factory(
        SchemaStore,
        transaction_context=transaction_context,
    )
    
    view_store = providers.Factory(
        ViewStore,
        transaction_context=transaction_context,
    )
    
    constraint_checker = providers.Factory(
        ConstraintChecker,
        safe_executor=safe_executor,
    )


class Engine:
    """Core AI-DB engine."""
    
    def __init__(self, container: DIContainer) -> None:
        self._container = container
        self._ai_agent = container.ai_agent()
        self._query_compiler = container.query_compiler()
        self._data_validator = container.data_validator()
    
    async def execute(
        self,
        query: str,
        permissions: PermissionLevel,
        transaction_context: TransactionProtocol,
        context: Optional[QueryContext] = None,
    ) -> QueryResult:
        """Execute a database query."""
        start_time = time.time()
        
        # Override container's transaction context
        self._container.transaction_context.override(transaction_context)
        
        # Create components for this transaction
        transaction_manager = self._container.transaction_manager()
        schema_store = self._container.schema_store()
        yaml_store = self._container.yaml_store()
        view_store = self._container.view_store()
        constraint_checker = self._container.constraint_checker()
        
        # Initialize context
        if context is None:
            context = QueryContext()
        
        try:
            # Load current schema
            context.schema = await schema_store.load_schema()
            
            # Analyze query with AI
            operation = await self._ai_agent.analyze_query(query, permissions, context)
            
            # Generate execution plan
            execution_plan = await self._ai_agent.generate_execution_plan(
                query, operation, context
            )
            
            # Check for errors in plan
            if execution_plan.error:
                return QueryResult(
                    status=False,
                    error=execution_plan.error,
                    transaction_id=transaction_context.id,
                    execution_time=time.time() - start_time,
                )
            
            # Execute based on operation type
            if operation.operation_type == "select":
                result = await self._execute_select(
                    operation, yaml_store, context
                )
            elif operation.operation_type in ["insert", "update", "delete"]:
                result = await self._execute_data_modification(
                    operation, yaml_store, schema_store, constraint_checker, context
                )
            elif operation.operation_type in ["create_table", "alter_table", "drop_table"]:
                result = await self._execute_schema_modification(
                    operation, schema_store, yaml_store, context
                )
            elif operation.operation_type in ["create_view", "drop_view"]:
                result = await self._execute_view_operation(
                    operation, view_store, yaml_store, schema_store, context
                )
            else:
                return QueryResult(
                    status=False,
                    error=f"Unknown operation type: {operation.operation_type}",
                    transaction_id=transaction_context.id,
                    execution_time=time.time() - start_time,
                )
            
            # Add common metadata
            result.transaction_id = transaction_context.id
            result.execution_time = time.time() - start_time
            result.ai_comment = execution_plan.interpretation if hasattr(execution_plan, 'interpretation') else None
            
            return result
            
        except PermissionError as e:
            return QueryResult(
                status=False,
                error=str(e),
                transaction_id=transaction_context.id,
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                status=False,
                error=str(e),
                transaction_id=transaction_context.id,
                execution_time=time.time() - start_time,
            )
    
    async def execute_compiled(
        self,
        compiled_plan: str,
        transaction_context: TransactionProtocol,
    ) -> QueryResult:
        """Execute a pre-compiled query plan."""
        start_time = time.time()
        
        # Override container's transaction context
        self._container.transaction_context.override(transaction_context)
        
        # Create components
        yaml_store = self._container.yaml_store()
        schema_store = self._container.schema_store()
        
        try:
            # Load current schema
            schema = await schema_store.load_schema()
            
            # Load table data
            table_data = {}
            for table_name in schema.tables:
                table_data[table_name] = await yaml_store.read_table(table_name)
            
            # Execute compiled query
            result_data = self._query_compiler.execute_compiled(compiled_plan, table_data)
            
            return QueryResult(
                status=True,
                data=result_data,
                transaction_id=transaction_context.id,
                execution_time=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Compiled query execution failed: {e}")
            return QueryResult(
                status=False,
                error=str(e),
                transaction_id=transaction_context.id,
                execution_time=time.time() - start_time,
            )
    
    async def _execute_select(
        self,
        operation: AIOperation,
        yaml_store: YAMLStore,
        context: QueryContext,
    ) -> QueryResult:
        """Execute a SELECT query."""
        # Load required table data
        table_data = {}
        for table_name in operation.affected_tables:
            table_data[table_name] = await yaml_store.read_table(table_name)
        
        # Compile the query
        if operation.python_code:
            compiled_plan = self._query_compiler.compile_query(operation.python_code)
            
            # Execute the query
            result_data = self._query_compiler.execute_compiled(compiled_plan, table_data)
            
            return QueryResult(
                status=True,
                data=result_data,
                compiled_plan=compiled_plan,
                data_loss_indicator=DataLossIndicator.NONE,
            )
        else:
            return QueryResult(
                status=False,
                error="No Python code generated for SELECT query",
            )
    
    async def _execute_data_modification(
        self,
        operation: AIOperation,
        yaml_store: YAMLStore,
        schema_store: SchemaStore,
        constraint_checker: ConstraintChecker,
        context: QueryContext,
    ) -> QueryResult:
        """Execute data modification (INSERT, UPDATE, DELETE)."""
        # Apply file updates
        for path, content in operation.file_updates.items():
            await yaml_store.write_file(path, content)
        
        # Validate if required
        if operation.validation_required and context.schema:
            errors = []
            all_tables_data = {}
            
            # Load all table data for constraint checking
            for table_name in context.schema.tables:
                all_tables_data[table_name] = await yaml_store.read_table(table_name)
            
            # Validate each affected table
            for table_name in operation.affected_tables:
                if table_name in context.schema.tables:
                    table = context.schema.tables[table_name]
                    table_data = all_tables_data.get(table_name, [])
                    
                    # Data validation
                    validation_errors = self._data_validator.validate_rows(table_data, table)
                    errors.extend(validation_errors)
                    
                    # Constraint checking
                    constraint_errors = await constraint_checker.check_constraints(
                        table, table_data, all_tables_data
                    )
                    errors.extend(constraint_errors)
            
            if errors:
                # Try to fix with AI
                context.recent_errors = errors[:5]  # Limit error context
                context.retry_count += 1
                
                fixed_plan = await self._ai_agent.handle_validation_error(
                    "\n".join(errors), operation, context
                )
                
                if fixed_plan and context.retry_count < context.max_retries:
                    # Retry with fixed plan
                    return await self._execute_data_modification(
                        operation, yaml_store, schema_store, constraint_checker, context
                    )
                else:
                    raise ValidationError("Data validation failed", errors[:10])
        
        # Determine data loss indicator
        data_loss = DataLossIndicator.NONE
        if operation.operation_type == "delete":
            data_loss = DataLossIndicator.YES
        elif operation.operation_type == "update":
            data_loss = DataLossIndicator.PROBABLE
        
        return QueryResult(
            status=True,
            data_loss_indicator=data_loss,
        )
    
    async def _execute_schema_modification(
        self,
        operation: AIOperation,
        schema_store: SchemaStore,
        yaml_store: YAMLStore,
        context: QueryContext,
    ) -> QueryResult:
        """Execute schema modification."""
        # Apply file updates
        for path, content in operation.file_updates.items():
            await yaml_store.write_file(path, content)
        
        # Determine data loss
        data_loss = DataLossIndicator.NONE
        if operation.operation_type == "drop_table":
            data_loss = DataLossIndicator.YES
        elif operation.operation_type == "alter_table":
            # Could potentially lose data depending on the alteration
            data_loss = DataLossIndicator.PROBABLE
        
        return QueryResult(
            status=True,
            data_loss_indicator=data_loss,
        )
    
    async def _execute_view_operation(
        self,
        operation: AIOperation,
        view_store: ViewStore,
        yaml_store: YAMLStore,
        schema_store: SchemaStore,
        context: QueryContext,
    ) -> QueryResult:
        """Execute view operation."""
        # Apply file updates
        for path, content in operation.file_updates.items():
            if path.endswith(".py") and operation.python_code:
                # Compile the view code to validate it
                compiled_plan = self._query_compiler.compile_query(operation.python_code)
                
                # Store as compiled plan in result
                return QueryResult(
                    status=True,
                    compiled_plan=compiled_plan,
                    data_loss_indicator=DataLossIndicator.NONE,
                )
        
        # Apply updates
        for path, content in operation.file_updates.items():
            await yaml_store.write_file(path, content)
        
        return QueryResult(
            status=True,
            data_loss_indicator=DataLossIndicator.NONE,
        )