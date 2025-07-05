"""Transaction-related tools for AI-DB."""

from typing import Any
import structlog

from .base import AIDBTool
from ...models.ai_db import (
    PermissionLevel,
    TransactionRequest,
    TransactionResponse,
)


class BeginTransactionTool(AIDBTool[TransactionRequest, TransactionResponse]):
    """Tool for beginning a new transaction."""
    
    @property
    def name(self) -> str:
        return "begin_transaction"
    
    @property
    def description(self) -> str:
        return "Start a new database transaction"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.DATA_MODIFY  # Minimum level for transactions
    
    @property
    def destructive_hint(self) -> bool:
        return False  # Beginning a transaction is not destructive
    
    async def execute(self, params: TransactionRequest) -> TransactionResponse:
        """Begin a new transaction."""
        self._logger.info("Beginning new transaction")
        
        try:
            # Start a new git-layer transaction
            transaction_id = await self._git_layer.begin_transaction()
            
            # Store the transaction context
            self.store_transaction(transaction_id, {
                "id": transaction_id,
                "active": True,
            })
            
            return TransactionResponse(
                status="success",
                transaction_id=transaction_id,
            )
        except Exception as e:
            self._logger.error("Failed to begin transaction", error=str(e))
            return TransactionResponse(
                status="error",
                error=str(e),
            )


class CommitTransactionTool(AIDBTool[TransactionRequest, TransactionResponse]):
    """Tool for committing a transaction."""
    
    @property
    def name(self) -> str:
        return "commit_transaction"
    
    @property
    def description(self) -> str:
        return "Commit an active database transaction"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.DATA_MODIFY
    
    @property
    def destructive_hint(self) -> bool:
        return True  # Committing makes changes permanent
    
    async def execute(self, params: TransactionRequest) -> TransactionResponse:
        """Commit a transaction."""
        if not params.transaction_id:
            return TransactionResponse(
                status="error",
                error="Transaction ID is required",
            )
        
        self._logger.info(
            "Committing transaction",
            transaction_id=params.transaction_id,
        )
        
        try:
            # Get transaction context
            context = self.get_transaction_context(params.transaction_id)
            if not context:
                return TransactionResponse(
                    status="error",
                    error=f"Transaction {params.transaction_id} not found",
                )
            
            # Commit via git-layer
            commit_message = params.commit_message or f"Commit transaction {params.transaction_id}"
            await self._git_layer.commit_transaction(params.transaction_id, commit_message)
            
            # Clean up transaction
            self.remove_transaction(params.transaction_id)
            
            return TransactionResponse(
                status="success",
                transaction_id=params.transaction_id,
            )
        except Exception as e:
            self._logger.error(
                "Failed to commit transaction",
                transaction_id=params.transaction_id,
                error=str(e),
            )
            return TransactionResponse(
                status="error",
                error=str(e),
            )


class RollbackTransactionTool(AIDBTool[TransactionRequest, TransactionResponse]):
    """Tool for rolling back a transaction."""
    
    @property
    def name(self) -> str:
        return "rollback_transaction"
    
    @property
    def description(self) -> str:
        return "Rollback an active database transaction"
    
    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.DATA_MODIFY
    
    @property
    def destructive_hint(self) -> bool:
        return False  # Rollback discards changes
    
    async def execute(self, params: TransactionRequest) -> TransactionResponse:
        """Rollback a transaction."""
        if not params.transaction_id:
            return TransactionResponse(
                status="error",
                error="Transaction ID is required",
            )
        
        self._logger.info(
            "Rolling back transaction",
            transaction_id=params.transaction_id,
        )
        
        try:
            # Get transaction context
            context = self.get_transaction_context(params.transaction_id)
            if not context:
                return TransactionResponse(
                    status="error",
                    error=f"Transaction {params.transaction_id} not found",
                )
            
            # Rollback via git-layer
            await self._git_layer.rollback_transaction(params.transaction_id)
            
            # Clean up transaction
            self.remove_transaction(params.transaction_id)
            
            return TransactionResponse(
                status="success",
                transaction_id=params.transaction_id,
            )
        except Exception as e:
            self._logger.error(
                "Failed to rollback transaction",
                transaction_id=params.transaction_id,
                error=str(e),
            )
            return TransactionResponse(
                status="error",
                error=str(e),
            )