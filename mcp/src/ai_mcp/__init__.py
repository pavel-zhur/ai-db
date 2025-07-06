"""MCP servers for AI-DB and AI-Frontend."""

__version__ = "0.1.0"

# Export main server creation functions
from .ai_db_server import create_ai_db_server
from .ai_frontend_server import create_ai_frontend_server

# Export configuration classes
from .config import AIDBMCPConfig, AIFrontendMCPConfig, MCPServerConfig

# Export protocols for type hints
from .protocols import (
    AIDBProtocol,
    AIFrontendProtocol,
    GenerationResult,
    GitLayerProtocol,
    QueryResult,
)

__all__ = [
    "__version__",
    "create_ai_db_server",
    "create_ai_frontend_server",
    "AIDBMCPConfig",
    "AIFrontendMCPConfig",
    "MCPServerConfig",
    "AIDBProtocol",
    "AIFrontendProtocol",
    "GitLayerProtocol",
    "QueryResult",
    "GenerationResult",
]
