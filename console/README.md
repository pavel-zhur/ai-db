# Console

An interactive natural language console interface for AI-DB and AI-Frontend, providing a chat-based experience for database operations and UI generation.

## Features

- **Natural Language Interface**: Chat with your database using plain English or SQL
- **Transaction Management**: Explicit BEGIN/COMMIT/ROLLBACK support with visual indicators
- **Multiple Output Formats**: View results as tables, JSON, or YAML
- **UI Generation**: Generate React frontends using natural language descriptions
- **Rich Terminal UI**: Interactive interface with syntax highlighting and progress indicators
- **Session History**: Complete conversation tracking with trace logging
- **Safety Features**: Confirmation prompts for destructive operations

## Installation

### From Source

```bash
cd console
pip install -e ".[dev]"
```

### Using Docker

```bash
docker build -t ai-console .
docker run -it -v $(pwd)/data:/data ai-console
```

## Usage

### Starting the Console

```bash
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
  max_iterations: 5
  timeout_seconds: 300

ai_frontend:
  claude_code_path: claude
  max_iterations: 5
  timeout_seconds: 300

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
export AI_DB_MAX_ITERATIONS=5

# AI-Frontend settings
export AI_FRONTEND_CLAUDE_CODE_PATH=claude

# Git-Layer settings
export GIT_LAYER_REPO_PATH=./data

# Console settings
export CONSOLE_DEBUG=true
export CONSOLE_LOG_FILE=console.log
export CONSOLE_TRACE_FILE=console_trace.log
```

## Architecture

The console integrates three main components:

1. **AI-DB**: Natural language database engine
2. **AI-Frontend**: UI generation via Claude Code CLI
3. **Git-Layer**: Transaction management with Git

### Key Components

- **ConsoleInterface**: Main interactive loop and command handling
- **CommandParser**: Parses user input and detects command types
- **OutputFormatter**: Formats query results in various formats
- **SessionState**: Maintains conversation history and transaction state
- **TraceLogger**: Logs all interactions for debugging

### Transaction Flow

1. User starts a transaction with `begin`
2. Git-Layer creates a branch for isolation
3. All operations occur within the transaction context
4. `commit` merges changes to main branch
5. `rollback` abandons the branch

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=console

# Run specific test file
pytest tests/test_command_parser.py
```

### Code Quality

```bash
# Format code
black src tests

# Type checking
mypy src

# Linting
ruff src tests
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