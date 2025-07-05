"""AI-Frontend MCP Server implementation."""

import asyncio
from typing import Any
import structlog
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import AIFrontendConfig
from .tools.ai_frontend import GenerateFrontendTool, GetFrontendInfoTool


def setup_logging(config: AIFrontendConfig) -> structlog.BoundLogger:
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


async def create_ai_frontend_server(config: AIFrontendConfig) -> Server:
    """Create and configure the AI-Frontend MCP server."""
    logger = setup_logging(config)
    logger.info("Starting AI-Frontend MCP server", version=config.server_version)
    
    # Initialize dependencies
    if config.use_mocks:
        logger.info("Using mock implementations")
        from .mocks import MockAIFrontend, MockGitLayer
        ai_frontend = MockAIFrontend()
        git_layer = MockGitLayer(config.git_repo_path)
    else:
        # Import real implementations when available
        # from ai_frontend import AIFrontend
        # from git_layer import GitLayer
        # ai_frontend = AIFrontend(config.ai_frontend_config_path)
        # git_layer = GitLayer(config.git_repo_path)
        logger.error("Real implementations not available, use --use-mocks flag")
        raise RuntimeError("Real AI-Frontend and Git-Layer implementations not available")
    
    # Create MCP server
    app = Server(config.server_name)
    
    # Initialize tools
    generate_tool = GenerateFrontendTool(ai_frontend, git_layer, logger)
    info_tool = GetFrontendInfoTool(ai_frontend, logger)
    
    tools = {
        "generate_frontend": generate_tool,
        "get_frontend_info": info_tool,
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
            if name == "generate_frontend":
                from .models.ai_frontend import FrontendRequest
                params = FrontendRequest(**arguments)
                result = await tool.execute(params)
            elif name == "get_frontend_info":
                result = await tool.execute({})
            else:
                raise ValueError(f"Unknown tool: {name}")
            
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
        "generate_frontend": {
            "request": {"type": "string", "description": "Natural language request for frontend generation/modification"},
            "transaction_id": {"type": "string", "description": "Optional transaction ID"},
        },
        "get_frontend_info": {},
    }
    return schemas.get(tool_name, {})


def _get_required_fields(tool_name: str) -> list[str]:
    """Get required fields for a tool."""
    required = {
        "generate_frontend": ["request"],
        "get_frontend_info": [],
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
        description="AI-Frontend MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  AI_FRONTEND_USE_MOCKS        Use mock implementations (default: false)
  AI_FRONTEND_LOG_LEVEL        Log level (default: INFO)
  AI_FRONTEND_LOG_FORMAT       Log format: json or console (default: json)
  AI_FRONTEND_GIT_REPO_PATH    Git repository path (default: /workspace/frontend)
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
        version="AI-Frontend MCP Server 0.1.0",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = AIFrontendConfig()
    
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