# Console

An interactive natural language console interface for AI-DB and AI-Frontend, providing a chat-based experience for database operations and UI generation. This is a Phase 2 POC implementation that demonstrates the complete AI-DB ecosystem integration.

## Features

- **Natural Language Interface**: Chat with your database using plain English or SQL
- **Git-based Transaction Management**: Explicit BEGIN/COMMIT/ROLLBACK with full Git transaction isolation
- **Multiple Output Formats**: View results as tables, JSON, or YAML with Rich formatting
- **Frontend Generation**: Generate React/TypeScript frontends using Claude Code integration
- **Rich Terminal UI**: Interactive interface with progress indicators, syntax highlighting, and real-time feedback
- **Session History**: Complete conversation tracking with markdown trace logging
- **Safety Features**: Confirmation prompts for destructive operations with smart detection
- **Async Architecture**: Non-blocking operations with proper progress feedback
- **Hierarchical Configuration**: Environment variables override config files with full validation

## Installation

### Prerequisites

- Python 3.13+
- Poetry (for dependency management)
- Git (for transaction management)
- Claude Code CLI (for frontend generation)

### From Source

```bash
cd console
poetry install
```

### Using Docker

```bash
docker build -t ai-console .
docker run -it -v $(pwd)/data:/data ai-console
```

## Usage

### Starting the Console

```bash
# Run with Poetry
poetry run console

# Run with default configuration
console

# Run with custom config file
console --config myconfig.yaml

# Run in debug mode
console --debug

# Specify data directory
console --repo-path ./mydata
```

### Basic Commands

#### Natural Language Queries
```
> Show all users
> Create a customers table with id, name, email, and created_at
> Add customer John Doe with email john@example.com
> Find all orders from last month
```

#### SQL Queries
```
> SELECT * FROM products WHERE price > 100
> INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')
> CREATE VIEW active_users AS SELECT * FROM users WHERE active = true
```

#### Transaction Management
```
> begin                  # Start a transaction
> ... make changes ...
> commit                 # Commit changes
> rollback              # Or rollback changes
```

#### UI Generation
```
> Generate a dashboard for customer management
> Create a form for product entry
> Build an interface showing sales analytics
```

#### Output Formatting
```
> output format json     # Switch to JSON output
> output format yaml     # Switch to YAML output
> output format table    # Switch back to table format (default)
```

#### Exporting Data
```
> export SELECT * FROM users to users.json
> export show all products to products.csv
```

#### Other Commands
```
> help                   # Show help
> exit                   # Exit console
```

## Configuration

### Configuration File (console.yaml)

```yaml
ai_db:
  api_base: https://api.openai.com/v1
  api_key: your-api-key
  model: gpt-4
  temperature: 0.0
  max_retries: 3
  timeout_seconds: 30.0

ai_frontend:
  claude_code_path: claude
  claude_code_docker_image: anthropics/claude-code:latest
  max_iterations: 5
  timeout_seconds: 300
  retry_attempts: 2
  api_base_url: http://localhost:8000

git_layer:
  repo_path: ./data

console:
  log_file: console.log
  trace_file: console_trace.log
  debug_mode: false
  default_output_format: table
  table_max_width: 120
  page_size: 50
```

### Environment Variables

```bash
# AI-DB settings
export AI_DB_API_BASE=https://api.openai.com/v1
export AI_DB_API_KEY=your-api-key
export AI_DB_MODEL=gpt-4
export AI_DB_TEMPERATURE=0.0
export AI_DB_MAX_RETRIES=3

# AI-Frontend settings
export AI_FRONTEND_CLAUDE_CODE_PATH=claude
export AI_FRONTEND_CLAUDE_CODE_DOCKER_IMAGE=anthropics/claude-code:latest
export AI_FRONTEND_API_BASE_URL=http://localhost:8000

# Git-Layer settings
export GIT_LAYER_REPO_PATH=./data

# Console settings
export CONSOLE_DEBUG=true
export CONSOLE_LOG_FILE=console.log
export CONSOLE_TRACE_FILE=console_trace.log
```

## Architecture

The console integrates three main library components following Phase 2 standardization:

1. **AI-DB**: Natural language database engine with async operations
2. **AI-Frontend**: React/TypeScript UI generation via Claude Code CLI
3. **Git-Layer**: Git-based transaction management with full isolation
4. **AI-Shared**: Common protocols and interfaces for loose coupling

### Key Components

- **ConsoleInterface**: Main interactive loop with dependency injection
- **CommandParser**: Natural language and SQL command detection with pattern matching
- **OutputFormatter**: Rich formatting for table, JSON, and YAML output
- **SessionState**: Transaction and conversation history management
- **TraceLogger**: Structured logging with markdown session traces
- **Config**: Hierarchical configuration with Pydantic validation

### Transaction Flow (Phase 2 Implementation)

1. User starts transaction with `begin` command
2. Git-Layer creates isolated branch in temporary working directory
3. All AI-DB and AI-Frontend operations use TransactionProtocol
4. Operations call `operation_complete()` or `operation_failed()` for Git tracking
5. `commit` merges changes to main branch and pushes
6. `rollback` creates rollback branch for debugging, cleans working directory
7. Automatic cleanup and error handling with proper async context management

## Development

### Running Tests

```bash
# Install development dependencies
poetry install

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=console

# Run specific test file
poetry run pytest tests/test_command_parser.py

# Run tests with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking (strict mode)
poetry run mypy .

# Linting
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check . --fix
```

### Project Structure

```
console/
├── src/
│   └── console/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── console_interface.py # Main console logic
│       ├── command_parser.py    # Command parsing
│       ├── output_formatter.py  # Result formatting
│       ├── config.py           # Configuration management
│       ├── logging.py          # Logging setup
│       └── models.py           # Data models
├── tests/
│   ├── conftest.py            # Test fixtures
│   ├── test_*.py              # Test files
│   └── ...
├── pyproject.toml             # Project configuration
├── Dockerfile                 # Container configuration
└── README.md                  # This file
```

## License

MIT