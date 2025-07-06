"""Protocol interfaces for dependencies.

This module contains protocol definitions for the actual library interfaces
that MCP tools need to work with. These protocols define the contract that
ai-db, ai-frontend, and git-layer libraries implement.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai_shared.protocols import TransactionProtocol

from .models.ai_db import DataLossIndicator, PermissionLevel


@runtime_checkable
class QueryResult(Protocol):
    """Protocol matching ai-db QueryResult."""

    status: bool
    data: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    execution_time: float
    compiled_plan: Optional[str]
    data_loss_indicator: DataLossIndicator


@runtime_checkable
class GenerationResult(Protocol):
    """Protocol matching ai-frontend GenerationResult."""

    success: bool
    output_path: Optional[Path]
    error: Optional[str]
    compiled: bool
    iterations_used: int


@runtime_checkable
class AIDBProtocol(Protocol):
    """Protocol for AI-DB library interface."""

    async def execute(
        self,
        query: str,
        permissions: PermissionLevel,
        transaction: TransactionProtocol,
        context: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Execute a query with specified permission level."""
        ...

    async def compile_query(
        self,
        query: str,
        transaction: TransactionProtocol,
    ) -> str:
        """Compile a query to a reusable plan."""
        ...

    async def execute_compiled(
        self,
        compiled_plan: str,
        transaction: TransactionProtocol,
    ) -> QueryResult:
        """Execute a pre-compiled query plan."""
        ...

    async def get_schema(self, transaction: TransactionProtocol) -> Dict[str, Any]:
        """Get current database schema."""
        ...

    async def init_from_folder(
        self,
        transaction: TransactionProtocol,
        source_folder: Path,
    ) -> None:
        """Initialize database from existing folder."""
        ...


@runtime_checkable
class AIFrontendProtocol(Protocol):
    """Protocol for AI-Frontend library interface."""

    async def generate_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction: TransactionProtocol,
        project_name: str,
    ) -> GenerationResult:
        """Generate a complete frontend from natural language request."""
        ...

    async def update_frontend(
        self,
        request: str,
        schema: Dict[str, Any],
        transaction: TransactionProtocol,
    ) -> GenerationResult:
        """Update an existing frontend based on natural language request."""
        ...

    async def get_schema(self, transaction: TransactionProtocol) -> Optional[Dict[str, Any]]:
        """Get the current frontend schema."""
        ...

    async def init_from_folder(
        self,
        source_path: Path,
        transaction: TransactionProtocol,
    ) -> None:
        """Initialize frontend from a seed folder."""
        ...


@runtime_checkable
class GitLayerProtocol(Protocol):
    """Protocol for Git-Layer library interface."""

    async def begin(
        self,
        repo_path: Path,
        message: str,
    ) -> TransactionProtocol:
        """Begin a new transaction."""
        ...

    async def recover(self, repo_path: Path) -> None:
        """Recover repository to clean state."""
        ...
