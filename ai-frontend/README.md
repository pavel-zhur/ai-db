# AI-Frontend

AI-managed React frontend generation for AI-DB. This library uses Claude Code CLI as the generation engine to build and modify UI components based on database schemas.

## Installation

```bash
pip install ai-frontend
```

## Requirements

- Python 3.10+
- Claude Code CLI installed and configured
- Node.js 18+ (for generated frontend compilation)

## Usage

```python
import asyncio
from ai_frontend import AiFrontend
from ai_frontend.config import AiFrontendConfig

async def main():
    config = AiFrontendConfig(
        claude_code_path="claude",  # Path to Claude Code CLI
        max_iterations=5,
        timeout_seconds=300
    )
    
    frontend = AiFrontend(config)
    
    # Generate a new frontend based on schema
    result = await frontend.generate_frontend(
        request="Create a dashboard for user management with tables and forms",
        schema=db_schema,  # AI-DB schema
        transaction_context=git_transaction  # From git-layer
    )
    
    if result.success:
        print(f"Frontend generated at: {result.output_path}")
    else:
        print(f"Generation failed: {result.error}")

asyncio.run(main())
```

## Features

- Natural language frontend generation via Claude Code CLI
- Automatic TypeScript type generation from AI-DB schemas
- Material-UI component library integration
- Vite-based build system with hot reload
- Transaction support via git-layer
- Compilation validation before committing changes
- Chrome MCP integration for visual feedback during development

## Architecture

The library acts as a bridge between AI-DB schemas and Claude Code CLI, managing the generation process and ensuring valid React/TypeScript output. All generated frontends are self-contained static sites that communicate with AI-DB via API calls.