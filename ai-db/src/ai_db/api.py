"""Public API for AI-DB."""

import logging
from typing import Optional
from dependency_injector.wiring import Provide, inject

from ai_db.core.models import (
    PermissionLevel,
    QueryResult,
    QueryContext,
    TransactionContext,
)
from ai_db.core.engine import Engine, DIContainer
from ai_db.config import get_config
from ai_db.exceptions import AIDBError

logger = logging.getLogger(__name__)


class AIDB:
    """Main AI-DB interface."""
    
    def __init__(self) -> None:
        """Initialize AI-DB."""
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, get_config().log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize DI container
        self._container = DIContainer()
        self._container.config.from_dict(get_config().__dict__)
        
        # Create engine
        self._engine = Engine(self._container)
        
        logger.info("AI-DB initialized")
    
    async def execute(
        self,
        query: str,
        permissions: PermissionLevel,
        transaction: TransactionContext,
        context: Optional[QueryContext] = None,
    ) -> QueryResult:
        """
        Execute a database query.
        
        Args:
            query: Natural language query or SQL
            permissions: Permission level for the operation
            transaction: Transaction context from git-layer
            context: Optional query context with schema and error history
            
        Returns:
            QueryResult with status, data, and metadata
        """
        if not query:
            return QueryResult(
                status=False,
                error="Query cannot be empty",
                transaction_id=transaction.transaction_id,
            )
        
        try:
            logger.info(f"Executing query with {permissions.value} permissions: {query[:100]}...")
            
            result = await self._engine.execute(
                query=query,
                permissions=permissions,
                transaction_context=transaction,
                context=context,
            )
            
            if result.status:
                logger.info("Query executed successfully")
            else:
                logger.warning(f"Query failed: {result.error}")
            
            return result
            
        except AIDBError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return QueryResult(
                status=False,
                error=f"Unexpected error: {str(e)}",
                transaction_id=transaction.transaction_id,
            )
    
    def execute_compiled(
        self,
        compiled_plan: str,
        transaction: TransactionContext,
    ) -> QueryResult:
        """
        Execute a pre-compiled query plan.
        
        Args:
            compiled_plan: Serialized query plan from previous compilation
            transaction: Transaction context from git-layer
            
        Returns:
            QueryResult with query results
        """
        import asyncio
        
        try:
            logger.info("Executing compiled query plan")
            
            # Run async method in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If called from async context
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._engine.execute_compiled(compiled_plan, transaction)
                    )
                    return future.result()
            else:
                # If called from sync context
                return asyncio.run(
                    self._engine.execute_compiled(compiled_plan, transaction)
                )
                
        except AIDBError:
            raise
        except Exception as e:
            logger.error(f"Failed to execute compiled query: {e}")
            return QueryResult(
                status=False,
                error=f"Failed to execute compiled query: {str(e)}",
                transaction_id=transaction.transaction_id,
            )
    
    async def begin_transaction(self, transaction: TransactionContext) -> None:
        """
        Begin a new transaction.
        
        This is handled by git-layer, but AI-DB can perform any necessary setup.
        
        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Beginning transaction {transaction.transaction_id}")
        # Any AI-DB specific transaction initialization can go here
    
    async def commit_transaction(self, transaction: TransactionContext) -> None:
        """
        Commit a transaction.
        
        This is handled by git-layer, but AI-DB can perform any necessary cleanup.
        
        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Committing transaction {transaction.transaction_id}")
        # Any AI-DB specific transaction cleanup can go here
    
    async def rollback_transaction(self, transaction: TransactionContext) -> None:
        """
        Rollback a transaction.
        
        This is handled by git-layer, but AI-DB can perform any necessary cleanup.
        
        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Rolling back transaction {transaction.transaction_id}")
        # Any AI-DB specific transaction cleanup can go here