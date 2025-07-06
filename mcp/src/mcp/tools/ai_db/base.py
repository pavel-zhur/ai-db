"""Base class for AI-DB tools."""

from typing import Any, Optional, TypeVar, Generic, TYPE_CHECKING
from abc import ABC, abstractmethod
import structlog
from pydantic import BaseModel

from ...models.ai_db import PermissionLevel

if TYPE_CHECKING:
    from ...protocols import AIDBProtocol, GitLayerProtocol

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class AIDBTool(ABC, Generic[T, R]):
    """Base class for AI-DB tools."""
    
    def __init__(self, ai_db: "AIDBProtocol", git_layer: "GitLayerProtocol", logger: Optional[structlog.BoundLogger] = None) -> None:
        """Initialize the tool."""
        self._ai_db = ai_db
        self._git_layer = git_layer
        self._logger = logger or structlog.get_logger()
        self._transactions: dict[str, Any] = {}
    
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
    
    def get_transaction_context(self, transaction_id: Optional[str]) -> Optional[Any]:
        """Get transaction context if available."""
        if transaction_id:
            return self._transactions.get(transaction_id)
        return None
    
    def store_transaction(self, transaction_id: str, context: Any) -> None:
        """Store transaction context."""
        self._transactions[transaction_id] = context
    
    def remove_transaction(self, transaction_id: str) -> None:
        """Remove transaction context."""
        self._transactions.pop(transaction_id, None)
    
    @abstractmethod
    async def execute(self, params: T) -> R:
        """Execute the tool."""
        ...