"""AI-DB MCP Server implementation."""

import asyncio
from typing import Any, Optional
import structlog
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import AIDBConfig
from .tools.ai_db import (
    SchemaModifyTool,
    DataModifyTool,
    SelectTool,
    ViewModifyTool,
    ExecuteCompiledTool,
    BeginTransactionTool,
    CommitTransactionTool,
    RollbackTransactionTool,
    GetSchemaTool,
)


def setup_logging(config: AIDBConfig) -> structlog.BoundLogger:
    """Set up structured logging."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if config.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


async def create_ai_db_server(config: AIDBConfig) -> Server:
    """Create and configure the AI-DB MCP server."""
    logger = setup_logging(config)
    logger.info("Starting AI-DB MCP server", version=config.server_version)
    
    # Initialize dependencies
    if config.use_mocks:
        logger.info("Using mock implementations")
        from .mocks import MockAIDB, MockGitLayer
        ai_db = MockAIDB()
        git_layer = MockGitLayer(config.git_repo_path)
    else:
        # Import real implementations when available
        # from ai_db import AIDB
        # from git_layer import GitLayer
        # ai_db = AIDB(config.ai_db_config_path)
        # git_layer = GitLayer(config.git_repo_path)
        logger.error("Real implementations not available, use --use-mocks flag")
        raise RuntimeError("Real AI-DB and Git-Layer implementations not available")
    
    # Create MCP server
    app = Server(config.server_name)
    
    # Initialize tools
    tools = {
        "schema_modify": SchemaModifyTool(ai_db, git_layer, logger),
        "data_modify": DataModifyTool(ai_db, git_layer, logger),
        "select": SelectTool(ai_db, git_layer, logger),
        "view_modify": ViewModifyTool(ai_db, git_layer, logger),
        "execute_compiled": ExecuteCompiledTool(ai_db, git_layer, logger),
        "begin_transaction": BeginTransactionTool(ai_db, git_layer, logger),
        "commit_transaction": CommitTransactionTool(ai_db, git_layer, logger),
        "rollback_transaction": RollbackTransactionTool(ai_db, git_layer, logger),
        "get_schema": GetSchemaTool(ai_db, git_layer, logger),
    }
    
    # Share transaction state between tools
    transaction_state = {}
    for tool in tools.values():
        if hasattr(tool, "_transactions"):
            tool._transactions = transaction_state
    
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema={
                    "type": "object",
                    "properties": _get_tool_schema(tool.name),
                    "required": _get_required_fields(tool.name),
                },
                **_get_tool_hints(tool),
            )
            for tool in tools.values()
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        """Execute a tool."""
        logger.info("Executing tool", tool=name)
        
        if name not in tools:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}",
                isError=True,
            )]
        
        tool = tools[name]
        
        try:
            # Map arguments to appropriate request model
            if name in ["schema_modify", "data_modify", "select", "view_modify"]:
                from .models.ai_db import QueryRequest
                params = QueryRequest(**arguments)
            elif name == "execute_compiled":
                from .models.ai_db import QueryRequest
                params = QueryRequest(
                    query=arguments.get("compiled_plan", ""),
                    transaction_id=arguments.get("transaction_id"),
                )
            elif name in ["begin_transaction", "commit_transaction", "rollback_transaction"]:
                from .models.ai_db import TransactionRequest
                params = TransactionRequest(**arguments)
            elif name == "get_schema":
                from .models.ai_db import SchemaRequest
                params = SchemaRequest(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            # Execute the tool
            result = await tool.execute(params)
            
            # Format response
            if hasattr(result, "error") and result.error:
                return [types.TextContent(
                    type="text",
                    text=f"Error: {result.error}",
                    isError=True,
                )]
            
            # Convert result to dict for JSON serialization
            result_dict = result.model_dump(exclude_none=True)
            
            return [types.TextContent(
                type="text",
                text=str(result_dict),
            )]
            
        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return [types.TextContent(
                type="text",
                text=f"Tool execution failed: {str(e)}",
                isError=True,
            )]
    
    return app


def _get_tool_schema(tool_name: str) -> dict[str, Any]:
    """Get the schema for a tool's parameters."""
    schemas = {
        "schema_modify": {
            "query": {"type": "string", "description": "Natural language schema modification query"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "data_modify": {
            "query": {"type": "string", "description": "Natural language data modification query"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "select": {
            "query": {"type": "string", "description": "Natural language select query"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "view_modify": {
            "query": {"type": "string", "description": "Natural language view modification query"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "execute_compiled": {
            "compiled_plan": {"type": "string", "description": "Pre-compiled query plan to execute"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "begin_transaction": {},
        "commit_transaction": {
            "transaction_id": {"type": "string", "description": "Transaction ID to commit"},
            "commit_message": {"type": "string", "description": "Optional commit message"},
        },
        "rollback_transaction": {
            "transaction_id": {"type": "string", "description": "Transaction ID to rollback"},
        },
        "get_schema": {
            "include_semantic_docs": {"type": "boolean", "description": "Include semantic documentation", "default": True},
        },
    }
    return schemas.get(tool_name, {})


def _get_required_fields(tool_name: str) -> list[str]:
    """Get required fields for a tool."""
    required = {
        "schema_modify": ["query"],
        "data_modify": ["query"],
        "select": ["query"],
        "view_modify": ["query"],
        "execute_compiled": ["compiled_plan"],
        "begin_transaction": [],
        "commit_transaction": ["transaction_id"],
        "rollback_transaction": ["transaction_id"],
        "get_schema": [],
    }
    return required.get(tool_name, [])


def _get_tool_hints(tool: Any) -> dict[str, Any]:
    """Get tool hints."""
    hints = {}
    if hasattr(tool, "destructive_hint"):
        hints["destructiveHint"] = tool.destructive_hint
    if hasattr(tool, "read_only_hint"):
        hints["readOnlyHint"] = tool.read_only_hint
    return hints


async def main() -> None:
    """Main entry point."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="AI-DB MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  AI_DB_USE_MOCKS        Use mock implementations (default: false)
  AI_DB_LOG_LEVEL        Log level (default: INFO)
  AI_DB_LOG_FORMAT       Log format: json or console (default: json)
  AI_DB_GIT_REPO_PATH    Git repository path (default: /workspace/data)
        """.strip()
    )
    parser.add_argument(
        "--use-mocks",
        action="store_true",
        help="Use mock implementations for testing",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="AI-DB MCP Server 0.1.0",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = AIDBConfig()
    
    # Override with CLI args
    if args.use_mocks:
        config.use_mocks = True
    
    try:
        # Create server
        app = await create_ai_db_server(config)
        
        # Run with stdio transport
        async with stdio_server() as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options(),
            )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())