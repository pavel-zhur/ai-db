# AI-Frontend API Reference

## AiFrontend

The main class for generating React frontends.

### Constructor

```python
AiFrontend(config: AiFrontendConfig)
```

Creates a new AiFrontend instance with the specified configuration.

### Methods

#### generate_frontend

```python
async def generate_frontend(
    request: str,
    schema: Dict[str, Any],
    transaction_context: TransactionContext,
    project_name: str = "ai-frontend"
) -> GenerationResult
```

Generates a complete frontend based on natural language request.

**Parameters:**
- `request`: Natural language description of the frontend to generate
- `schema`: AI-DB schema dictionary in JSON Schema format
- `transaction_context`: Git-layer transaction context
- `project_name`: Name for the generated project

**Returns:**
- `GenerationResult` with success status and details

#### update_frontend

```python
async def update_frontend(
    request: str,
    schema: Dict[str, Any],
    transaction_context: TransactionContext
) -> GenerationResult
```

Updates an existing frontend based on natural language request.

**Parameters:**
- `request`: Natural language description of changes to make
- `schema`: Updated AI-DB schema dictionary
- `transaction_context`: Git-layer transaction context

**Returns:**
- `GenerationResult` with success status and details

## Configuration

### AiFrontendConfig

Configuration class for AI-Frontend operations.

```python
@dataclass
class AiFrontendConfig:
    # Claude Code CLI settings
    claude_code_path: str = "claude"
    claude_code_args: list[str] = ["--no-interactive"]
    max_iterations: int = 5
    timeout_seconds: int = 300

    # Frontend generation settings
    use_material_ui: bool = True
    use_vite: bool = True
    typescript_strict: bool = True
    
    # API configuration
    api_base_url: str = "http://localhost:8000"
    api_retry_attempts: int = 3
    api_retry_delay: float = 1.0
    
    # Chrome MCP settings
    enable_chrome_mcp: bool = True
    chrome_mcp_port: int = 9222
    
    # Build settings
    node_version: str = "18"
    npm_registry: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_claude_output: bool = True
```

## Data Types

### GenerationResult

Result of frontend generation operation.

```python
@dataclass
class GenerationResult:
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    compiled: bool = False
    iterations_used: int = 0
```

### TransactionContext

Transaction context from git-layer.

```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path
    commit_message_callback: Optional[callable] = None
```

## Exceptions

### AiFrontendError
Base exception for all ai-frontend errors.

### ClaudeCodeError
Raised when Claude Code CLI operations fail.

### CompilationError
Raised when frontend compilation fails.

### GenerationError
Raised when frontend generation fails.

### ConfigurationError
Raised for configuration issues.

### TransactionError
Raised for transaction-related issues.

## Schema Format

AI-DB schemas should follow JSON Schema format:

```python
schema = {
    "tables": {
        "table_name": {
            "columns": {
                "column_name": {
                    "type": "string|number|integer|boolean|array|object",
                    "format": "email|date|date-time|uuid",  # optional
                    "required": True|False,
                    "nullable": True|False,
                    "unique": True|False,
                    "primary_key": True|False,
                    "foreign_key": "other_table.column",
                    "auto_increment": True|False,
                    "generated": True|False,
                    "default": "value",
                    "enum": ["option1", "option2"],
                }
            }
        }
    },
    "views": {
        "view_name": {
            "result_schema": {
                "field_name": {
                    "type": "string",
                    "nullable": True|False
                }
            }
        }
    }
}
```