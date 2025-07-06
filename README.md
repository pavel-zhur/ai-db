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

## Docker Usage

The AI-DB system uses Docker for containerized deployment. All components are built from a shared base image with proper dependency management.

### Prerequisites
- Docker and Docker Compose installed
- Environment variables set (see `.env.example`)

### Building and Running

#### 1. Full System (All Components)
```bash
# Build all images
docker-compose build

# Start all services
docker-compose up

# Or run in background
docker-compose up -d
```

This starts:
- `ai-hub`: HTTP API server on port 8000
- `console`: Interactive terminal (attach with `docker attach`)
- `mcp-ai-db` & `mcp-ai-frontend`: MCP servers
- `nginx`: Web server on port 80

#### 2. Individual Components
```bash
# Build a specific component (from workspace root)
docker build -f ai-db/Dockerfile -t ai-db .
docker build -f console/Dockerfile -t console .

# Run individual component
docker run -it console
docker run -p 8000:8000 ai-hub
```

#### 3. Development Mode
```bash
# Run with volume mounts for live code changes
docker-compose -f docker-compose.dev.yml up

# Or use the test-runner for validation
docker-compose run test-runner
```

#### 4. Running Tests
```bash
# Run all tests in containers
docker-compose run test-runner

# Test a specific component
docker run --rm -it ai-db bash -c "poetry install && poetry run pytest"
```

### Common Operations

```bash
# View logs
docker-compose logs -f ai-hub
docker-compose logs -f console

# Connect to console interactively
docker-compose exec console bash

# Stop all services
docker-compose down

# Stop and remove volumes (clean data)
docker-compose down -v

# Rebuild after code changes
docker-compose build --no-cache ai-hub
```

### Environment Configuration

Create `.env` file from template:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Key environment variables:
- `AI_DB_API_KEY`: OpenAI API key for AI-DB
- `AI_FRONTEND_API_KEY`: Anthropic API key for frontend generation
- `GIT_LAYER_REPO_PATH`: Path for git repositories (default: ./data)

### Troubleshooting

- **Build fails with dependency errors**: Ensure you're building from workspace root, not component directory
- **Container can't find ai-shared**: Check that docker-compose uses correct build context
- **Permission errors**: The containers run as non-root user; ensure volume permissions are correct