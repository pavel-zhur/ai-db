"""Protocol interfaces for dependencies."""

from typing import Protocol, Optional, Any, runtime_checkable
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dataclasses import dataclass

from .models.ai_db import PermissionLevel, DataLossIndicator


@dataclass
class AIDBQueryResult:
    """Result from AI-DB query execution."""
    
    status: str
    data: Optional[list[dict[str, Any]]] = None
    schema: Optional[dict[str, Any]] = None
    data_loss_indicator: DataLossIndicator = DataLossIndicator.NONE
    ai_comment: str = ""
    compiled_plan: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AIFrontendResult:
    """Result from AI-Frontend generation."""
    
    status: str
    generated_files: Optional[list[str]] = None
    ai_comment: str = ""
    error: Optional[str] = None


@runtime_checkable
class AIDBProtocol(Protocol):
    """Protocol for AI-DB implementations."""
    
    async def execute(
        self,
        query: str,
        permission_level: PermissionLevel,
        transaction_context: Optional[Any] = None,
    ) -> AIDBQueryResult:
        """Execute a query with specified permission level."""
        ...
    
    async def execute_compiled(
        self,
        compiled_plan: str,
        transaction_context: Optional[Any] = None,
    ) -> AIDBQueryResult:
        """Execute a pre-compiled query plan."""
        ...
    
    async def get_schema(self, include_semantic_docs: bool = True) -> dict[str, Any]:
        """Get current database schema."""
        ...


@runtime_checkable
class AIFrontendProtocol(Protocol):
    """Protocol for AI-Frontend implementations."""
    
    async def generate(
        self,
        request: str,
        transaction_context: Optional[Any] = None,
    ) -> AIFrontendResult:
        """Generate frontend components from natural language."""
        ...
    
    async def get_frontend_info(self) -> dict[str, Any]:
        """Get information about frontend components."""
        ...


@runtime_checkable
class TransactionContext(Protocol):
    """Protocol for transaction context."""
    
    transaction_id: str
    working_directory: str
    
    async def write_escalation(self) -> str:
        """Escalate write permissions."""
        ...


@runtime_checkable
class GitLayerProtocol(Protocol):
    """Protocol for Git-Layer implementations."""
    
    @asynccontextmanager
    async def transaction(self, commit_message: Optional[str] = None) -> AsyncGenerator[TransactionContext, None]:
        """Create a transaction context."""
        ...
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        ...
    
    async def commit_transaction(self, transaction_id: str, commit_message: str) -> None:
        """Commit a transaction."""
        ...
    
    async def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a transaction."""
        ...