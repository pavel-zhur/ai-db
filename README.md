# AI-DB: An AI-Native Database and AI-Generated Frontend

## What is this?

AI-DB is a database where AI is the database engine itself, not just a translation layer. It also includes AI-generated frontends for analytics and data management.

You can communicate with it using natural language, SQL, or any programming language - C#, TypeScript, Python, anything. The AI interprets your intent and executes the appropriate operations.

## How it works

Traditional databases with AI:
```
You → SQL → Database → Results
You → AI → SQL → Database → Results  (adds translation layer)
```

AI-DB:
```
You → AI → Files → Results  (AI directly manipulates data)
```

## Key Features

1. **Any input language** - Natural language, SQL, C#, TypeScript, or any code
2. **AI-managed migrations** - Schema changes through conversation
3. **Git as storage layer** - Version control built-in
4. **Git as transaction engine** - Branches provide ACID properties
5. **Query compilation** - SELECT queries and views compile to Python for performance
6. **Safety features** - Permission levels and destructive operation confirmations
7. **Constraints** - Foreign keys, unique, check, and not-null constraints with AI-generated Python validation
8. **Session context** - Console remembers conversation history with trace logging

## Components

- **ai-db**: Core database engine using LangChain with OpenAI-compatible models for query interpretation and execution
- **console**: Interactive terminal interface with Rich UI, supporting natural language chat, multiple output formats, and transaction visualization
- **mcp**: Two Model Context Protocol servers (ai-db-mcp and ai-frontend-mcp) exposing database and UI generation as MCP tools
- **ai-frontend**: React/TypeScript generator using Claude Code CLI to create Material-UI dashboards through iterative refinement
- **git-layer**: Transaction system using Git branches and temporary clones for isolation and atomicity

## AI-Generated Frontend

The ai-frontend component allows you to generate and modify React UIs through natural language. Simply describe what you want - dashboards, forms, reports - and AI creates the components using Claude Code CLI. When your data schema changes, tell AI to update the UI accordingly. The generated frontend automatically understands your data structure and includes proper TypeScript types.

Features include:
- Material-UI components for professional analytics dashboards
- Automatic TypeScript type generation from database schemas
- Vite-based build system with hot module replacement
- API client generation expecting HTTP endpoints (requires separate API server)
- Build validation before committing changes
- Static site generation suitable for CDN deployment

## Storage

Data is stored as YAML files, which means you can:
- Read data directly
- Edit with any text editor
- Use version control
- Understand exactly what's stored

The AI interprets queries and generates Python code for execution. Data integrity is ensured through:
- JSON Schema validation for all data operations
- Constraint checking with AI-generated Python validators
- RestrictedPython sandbox for safe code execution
- Semantic documentation automatically maintained by AI
- Validation retry logic where AI attempts to fix constraint violations

Git-layer provides transaction isolation through:
- New branch creation for each transaction
- Temporary repository clones for write operations
- Atomic commits with descriptive messages
- Failed transactions preserved in branches for debugging
- Main branch always remains in clean, consistent state

## Status

This is a proof of concept exploring how databases might work when AI is the core engine rather than an add-on feature.