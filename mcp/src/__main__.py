"""Main entry point for the MCP package."""

import sys
import os


def main() -> None:
    """Main entry point."""
    # Get the script name from command line
    if len(sys.argv) < 1:
        print("Error: No command specified", file=sys.stderr)
        sys.exit(1)
    
    # Determine which server to run based on the command
    command = os.path.basename(sys.argv[0])
    
    if command == "ai-db-mcp" or "ai_db_server" in command:
        from .ai_db_server import main as ai_db_main
        import asyncio
        asyncio.run(ai_db_main())
    elif command == "ai-frontend-mcp" or "ai_frontend_server" in command:
        from .ai_frontend_server import main as ai_frontend_main
        import asyncio
        asyncio.run(ai_frontend_main())
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Use 'ai-db-mcp' or 'ai-frontend-mcp'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()