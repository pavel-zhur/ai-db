"""MCP servers for AI-DB and AI-Frontend."""

__version__ = "0.1.0"

# Export main server creation functions
from .ai_db_server import create_ai_db_server
from .ai_frontend_server import create_ai_frontend_server

# Export configuration classes
from .config import AIDBConfig, AIFrontendConfig, ServerConfig

# Export protocols for type hints
from .protocols import (
    AIDBProtocol,
    AIFrontendProtocol,
    GitLayerProtocol,
    TransactionContext,
    AIDBQueryResult,
    AIFrontendResult,
)

__all__ = [
    "__version__",
    "create_ai_db_server",
    "create_ai_frontend_server",
    "AIDBConfig",
    "AIFrontendConfig",
    "ServerConfig",
    "AIDBProtocol",
    "AIFrontendProtocol",
    "GitLayerProtocol",
    "TransactionContext",
    "AIDBQueryResult",
    "AIFrontendResult",
]