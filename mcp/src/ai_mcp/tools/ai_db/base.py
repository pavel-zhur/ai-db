"""Base class for AI-DB tools."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

import structlog
from ai_shared.protocols import TransactionProtocol

from ...models.ai_db import PermissionLevel

if TYPE_CHECKING:
    from ...config import AIDBMCPConfig
    from ...protocols import AIDBProtocol


class AIDBTool(ABC):
    """Base class for AI-DB tools."""

    def __init__(
        self,
        ai_db: "AIDBProtocol",
        git_layer: Any,
        config: "AIDBMCPConfig",
        logger: Optional[structlog.BoundLogger] = None,
    ) -> None:
        """Initialize the tool."""
        self._ai_db = ai_db
        self._git_layer = git_layer
        self._config = config
        self._logger = logger or structlog.get_logger()

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        ...

    @property
    @abstractmethod
    def permission_level(self) -> PermissionLevel:
        """Required permission level."""
        ...

    @property
    def destructive_hint(self) -> bool:
        """Whether this tool is potentially destructive."""
        return self.permission_level in (PermissionLevel.DATA_MODIFY, PermissionLevel.SCHEMA_MODIFY)

    @property
    def read_only_hint(self) -> bool:
        """Whether this tool only reads data."""
        return self.permission_level == PermissionLevel.SELECT

    @asynccontextmanager
    async def _create_transaction(self, message: str) -> AsyncGenerator[TransactionProtocol, None]:
        """Create a new transaction for operations."""
        if self._config.use_mocks:
            from ...mocks import MockTransaction

            transaction = MockTransaction(f"mock-{id(self)}", Path(self._config.repo_path))
            try:
                await transaction.write_escalation_required()
                yield transaction
                await transaction.operation_complete(message)
            except Exception as e:
                await transaction.operation_failed(str(e))
                raise
        else:
            # Use real git-layer
            transaction = await self._git_layer.begin(Path(self._config.repo_path), message)
            try:
                yield transaction
                # Transaction is auto-committed by git-layer context manager
            except Exception:
                # Transaction is auto-rolled back by git-layer context manager
                raise

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Any:
        """Execute the tool."""
        ...
