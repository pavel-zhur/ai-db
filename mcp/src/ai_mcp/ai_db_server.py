"""AI-DB MCP Server implementation."""

import asyncio
from typing import Any, Dict

import mcp.types as types
import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import AIDBMCPConfig
from .tools.ai_db import (
    CompileQueryTool,
    DataModifyTool,
    ExecuteCompiledTool,
    GetSchemaTool,
    InitFromFolderTool,
    SchemaModifyTool,
    SelectTool,
    ViewModifyTool,
)


def setup_logging(config: AIDBMCPConfig) -> structlog.BoundLogger:
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


async def create_ai_db_server(config: AIDBMCPConfig) -> Server:
    """Create and configure the AI-DB MCP server."""
    logger = setup_logging(config)
    logger.info("Starting AI-DB MCP server", version=config.server_version)

    # Initialize dependencies
    if config.use_mocks:
        logger.info("Using mock implementations")
        from .mocks import MockAIDB, MockGitLayer

        ai_db = MockAIDB()
        git_layer_module = MockGitLayer(config.repo_path)
    else:
        # Import real implementations
        import git_layer
        from ai_db import AIDB
        from ai_db.config import AIDBConfig

        logger.info("Using real AI-DB and Git-Layer implementations")

        # Let AI-DB read its own configuration from AI_DB_* environment variables
        ai_db_config = AIDBConfig()
        ai_db = AIDB(ai_db_config)

        # Git-layer is used through its begin() function - no instance needed
        git_layer_module = git_layer

    # Create MCP server
    app = Server(config.server_name)

    # Initialize tools
    tools = {
        "schema_modify": SchemaModifyTool(ai_db, git_layer_module, config, logger),
        "data_modify": DataModifyTool(ai_db, git_layer_module, config, logger),
        "select": SelectTool(ai_db, git_layer_module, config, logger),
        "view_modify": ViewModifyTool(ai_db, git_layer_module, config, logger),
        "execute_compiled": ExecuteCompiledTool(ai_db, git_layer_module, config, logger),
        "compile_query": CompileQueryTool(ai_db, git_layer_module, config, logger),
        "get_schema": GetSchemaTool(ai_db, git_layer_module, config, logger),
        "init_from_folder": InitFromFolderTool(ai_db, git_layer_module, config, logger),
    }

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
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        """Execute a tool."""
        logger.info("Executing tool", tool=name)

        if name not in tools:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                    isError=True,
                )
            ]

        tool = tools[name]

        try:
            # Execute the tool with arguments directly
            result = await tool.execute(arguments)

            # Format response based on result type
            if hasattr(result, "status") and not result.status:
                # Query result with error
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {result.error or 'Operation failed'}",
                        isError=True,
                    )
                ]
            elif hasattr(result, "success") and not result.success:
                # Generation result with error
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {result.error or 'Operation failed'}",
                        isError=True,
                    )
                ]

            # Convert result to dict for JSON serialization
            if hasattr(result, "model_dump"):
                result_dict = result.model_dump(exclude_none=True)
            else:
                result_dict = result.__dict__ if hasattr(result, "__dict__") else str(result)

            return [
                types.TextContent(
                    type="text",
                    text=str(result_dict),
                )
            ]

        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e), exc_info=True)
            return [
                types.TextContent(
                    type="text",
                    text=f"Tool execution failed: {str(e)}",
                    isError=True,
                )
            ]

    return app


def _get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get the schema for a tool's parameters."""
    schemas = {
        "schema_modify": {
            "query": {
                "type": "string",
                "description": "Natural language schema modification query",
            },
        },
        "data_modify": {
            "query": {"type": "string", "description": "Natural language data modification query"},
        },
        "select": {
            "query": {"type": "string", "description": "Natural language select query"},
        },
        "view_modify": {
            "query": {"type": "string", "description": "Natural language view modification query"},
        },
        "execute_compiled": {
            "compiled_plan": {
                "type": "string",
                "description": "Pre-compiled query plan to execute",
            },
        },
        "compile_query": {
            "query": {"type": "string", "description": "Query to compile for future reuse"},
        },
        "get_schema": {
            "include_semantic_docs": {
                "type": "boolean",
                "description": "Include semantic documentation",
                "default": True,
            },
        },
        "init_from_folder": {
            "source_folder": {
                "type": "string",
                "description": "Path to folder containing seed data",
            },
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
        "compile_query": ["query"],
        "get_schema": [],
        "init_from_folder": ["source_folder"],
    }
    return required.get(tool_name, [])


def _get_tool_hints(tool: Any) -> Dict[str, Any]:
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
        """.strip(),
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
    config = AIDBMCPConfig()

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
