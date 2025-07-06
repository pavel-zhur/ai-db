"""AI-Frontend MCP Server implementation."""

import asyncio
from typing import Any, Dict

import mcp.types as types
import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import AIFrontendMCPConfig
from .tools.ai_frontend import (
    GenerateFrontendTool,
    GetFrontendSchemaTool,
    InitFrontendFromFolderTool,
    UpdateFrontendTool,
)


def setup_logging(config: AIFrontendMCPConfig) -> structlog.BoundLogger:
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


async def create_ai_frontend_server(config: AIFrontendMCPConfig) -> Server:
    """Create and configure the AI-Frontend MCP server."""
    logger = setup_logging(config)
    logger.info("Starting AI-Frontend MCP server", version=config.server_version)

    # Initialize dependencies
    if config.use_mocks:
        logger.info("Using mock implementations")
        from .mocks import MockAIFrontend, MockGitLayer

        ai_frontend = MockAIFrontend()
        git_layer_module = MockGitLayer(config.repo_path)
    else:
        # Import real implementations
        import git_layer
        from ai_frontend import AiFrontend, AiFrontendConfig

        logger.info("Using real AI-Frontend and Git-Layer implementations")

        # Configure AI-Frontend
        ai_frontend_config = AiFrontendConfig(
            claude_code_docker_image=config.claude_code_docker_image,
            max_iterations=config.max_iterations,
            timeout_seconds=config.claude_code_timeout,
            retry_attempts=config.retry_attempts,
            api_base_url=config.api_base_url,
            use_material_ui=config.use_material_ui,
            typescript_strict=config.typescript_strict,
        )
        ai_frontend = AiFrontend(ai_frontend_config)

        # Git-layer is used through its begin() function - no instance needed
        git_layer_module = git_layer

    # Create MCP server
    app = Server(config.server_name)

    # Initialize tools
    tools = {
        "generate_frontend": GenerateFrontendTool(ai_frontend, git_layer_module, config, logger),
        "update_frontend": UpdateFrontendTool(ai_frontend, git_layer_module, config, logger),
        "get_frontend_schema": GetFrontendSchemaTool(ai_frontend, git_layer_module, config, logger),
        "init_frontend_from_folder": InitFrontendFromFolderTool(
            ai_frontend, git_layer_module, config, logger
        ),
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
            if hasattr(result, "success") and not result.success:
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
        "generate_frontend": {
            "request": {
                "type": "string",
                "description": "Natural language request for frontend generation",
            },
            "schema": {
                "type": "object",
                "description": "Database schema for TypeScript generation",
            },
            "project_name": {"type": "string", "description": "Name for the generated project"},
        },
        "update_frontend": {
            "request": {
                "type": "string",
                "description": "Natural language request for frontend modifications",
            },
            "schema": {"type": "object", "description": "Updated database schema"},
        },
        "get_frontend_schema": {},
        "init_frontend_from_folder": {
            "source_path": {
                "type": "string",
                "description": "Path to folder containing seed frontend files",
            },
        },
    }
    return schemas.get(tool_name, {})


def _get_required_fields(tool_name: str) -> list[str]:
    """Get required fields for a tool."""
    required = {
        "generate_frontend": ["request", "schema", "project_name"],
        "update_frontend": ["request", "schema"],
        "get_frontend_schema": [],
        "init_frontend_from_folder": ["source_path"],
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
        description="AI-Frontend MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  AI_FRONTEND_USE_MOCKS        Use mock implementations (default: false)
  AI_FRONTEND_LOG_LEVEL        Log level (default: INFO)
  AI_FRONTEND_LOG_FORMAT       Log format: json or console (default: json)
  AI_FRONTEND_GIT_REPO_PATH    Git repository path (default: /workspace/frontend)
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
        version="AI-Frontend MCP Server 0.1.0",
    )

    args = parser.parse_args()

    # Load configuration
    config = AIFrontendMCPConfig()

    # Override with CLI args
    if args.use_mocks:
        config.use_mocks = True

    try:
        # Create server
        app = await create_ai_frontend_server(config)

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
