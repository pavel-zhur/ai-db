"""Frontend generation tools."""

from typing import Any, Optional, TYPE_CHECKING
import structlog

from ...models.ai_frontend import (
    FrontendRequest,
    FrontendResponse,
    FrontendInfoResponse,
)

if TYPE_CHECKING:
    from ...protocols import AIFrontendProtocol, GitLayerProtocol


class GenerateFrontendTool:
    """Tool for generating/modifying frontend components."""
    
    def __init__(
        self,
        ai_frontend: "AIFrontendProtocol",
        git_layer: "GitLayerProtocol",
        logger: Optional[structlog.BoundLogger] = None,
    ) -> None:
        """Initialize the tool."""
        self._ai_frontend = ai_frontend
        self._git_layer = git_layer
        self._logger = logger or structlog.get_logger()
        self._transactions: dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        return "generate_frontend"
    
    @property
    def description(self) -> str:
        return "Generate or modify React frontend components using natural language"
    
    @property
    def destructive_hint(self) -> bool:
        return True  # Modifies files
    
    @property
    def read_only_hint(self) -> bool:
        return False
    
    def get_transaction_context(self, transaction_id: Optional[str]) -> Optional[Any]:
        """Get transaction context if available."""
        if transaction_id:
            return self._transactions.get(transaction_id)
        return None
    
    async def execute(self, params: FrontendRequest) -> FrontendResponse:
        """Generate frontend components."""
        self._logger.info(
            "Generating frontend",
            request=params.request,
            transaction_id=params.transaction_id,
        )
        
        try:
            transaction_context = self.get_transaction_context(params.transaction_id)
            result = await self._ai_frontend.generate(
                params.request,
                transaction_context,
            )
            
            return FrontendResponse(
                status=result.status,
                generated_files=result.generated_files,
                ai_comment=result.ai_comment,
                transaction_id=params.transaction_id,
                error=result.error,
            )
        except Exception as e:
            self._logger.error("Frontend generation failed", error=str(e))
            return FrontendResponse(
                status="error",
                ai_comment="Frontend generation failed",
                error=str(e),
            )


class GetFrontendInfoTool:
    """Tool for getting frontend information."""
    
    def __init__(
        self,
        ai_frontend: "AIFrontendProtocol",
        logger: Optional[structlog.BoundLogger] = None,
    ) -> None:
        """Initialize the tool."""
        self._ai_frontend = ai_frontend
        self._logger = logger or structlog.get_logger()
    
    @property
    def name(self) -> str:
        return "get_frontend_info"
    
    @property
    def description(self) -> str:
        return "Get information about generated frontend components and their semantic descriptions"
    
    @property
    def destructive_hint(self) -> bool:
        return False
    
    @property
    def read_only_hint(self) -> bool:
        return True
    
    async def execute(self, params: dict[str, Any]) -> FrontendInfoResponse:
        """Get frontend information."""
        self._logger.info("Getting frontend information")
        
        try:
            result = await self._ai_frontend.get_frontend_info()
            
            return FrontendInfoResponse(
                components=result["components"],
                semantic_docs=result["semantic_docs"],
            )
        except Exception as e:
            self._logger.error("Failed to get frontend info", error=str(e))
            return FrontendInfoResponse(
                components=[],
                semantic_docs={},
                error=str(e),
            )