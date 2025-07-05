# AI-DB API Reference

## Core Classes

### AIDB

The main interface for interacting with the AI-DB database engine.

```python
from ai_db import AIDB

db = AIDB()
```

#### Methods

##### `async execute(query: str, permissions: PermissionLevel, transaction: TransactionContext, context: Optional[QueryContext] = None) -> QueryResult`

Execute a database query using natural language, SQL, or any programming language.

**Parameters:**
- `query` (str): The query to execute in any language
- `permissions` (PermissionLevel): The permission level for this operation
- `transaction` (TransactionContext): Transaction context from git-layer
- `context` (Optional[QueryContext]): Optional context with schema and error history

**Returns:**
- `QueryResult`: Result object containing status, data, and metadata

**Example:**
```python
result = await db.execute(
    "SELECT * FROM users WHERE age > 18",
    PermissionLevel.SELECT,
    transaction
)
```

##### `execute_compiled(compiled_plan: str, transaction: TransactionContext) -> QueryResult`

Execute a pre-compiled query plan without AI processing.

**Parameters:**
- `compiled_plan` (str): Serialized query plan from a previous compilation
- `transaction` (TransactionContext): Transaction context from git-layer

**Returns:**
- `QueryResult`: Result object containing query results

**Example:**
```python
result = db.execute_compiled(compiled_plan, transaction)
```

### Enums

#### PermissionLevel

Permission levels for database operations:

```python
from ai_db import PermissionLevel

PermissionLevel.SELECT          # Read-only queries
PermissionLevel.DATA_MODIFY     # Insert, update, delete operations
PermissionLevel.SCHEMA_MODIFY   # Create, alter, drop tables
PermissionLevel.VIEW_MODIFY     # Create, modify views
```

#### DataLossIndicator

Indicates potential data loss from an operation:

```python
from ai_db import DataLossIndicator

DataLossIndicator.NONE      # No data loss
DataLossIndicator.PROBABLE  # Might lose data (e.g., UPDATE)
DataLossIndicator.YES       # Will lose data (e.g., DELETE, DROP)
```

### Data Models

#### QueryResult

Result of a query execution:

```python
@dataclass
class QueryResult:
    status: bool                              # Success/failure
    data: Optional[List[Dict[str, Any]]]     # Query results (for SELECT)
    schema: Optional[Dict[str, Any]]         # JSON Schema of results
    data_loss_indicator: DataLossIndicator   # Data loss indicator
    ai_comment: Optional[str]                # AI interpretation
    compiled_plan: Optional[str]             # Compiled query (for SELECT/views)
    transaction_id: Optional[str]            # Transaction ID
    error: Optional[str]                     # Error message if failed
    execution_time: Optional[float]          # Execution time in seconds
```

#### QueryContext

Context for query execution:

```python
@dataclass
class QueryContext:
    schema: Optional[Schema] = None          # Current database schema
    recent_errors: List[str] = []           # Recent error messages
    retry_count: int = 0                    # Current retry attempt
    max_retries: int = 3                    # Maximum retry attempts
```

#### TransactionContext

Transaction context (provided by git-layer):

```python
@dataclass
class TransactionContext:
    transaction_id: str                      # Unique transaction ID
    working_directory: str                   # Current working directory
    is_write_escalated: bool = False        # Whether writes are allowed
    
    def escalate_write(self) -> str:        # Request write access
        # Implemented by git-layer
```

## Configuration

AI-DB uses environment variables for configuration:

```bash
# AI Model Configuration
export AI_DB_API_BASE="https://api.openai.com/v1"
export AI_DB_API_KEY="your-api-key"
export AI_DB_MODEL="gpt-4"
export AI_DB_TEMPERATURE="0.0"

# Execution Configuration
export AI_DB_MAX_RETRIES="3"
export AI_DB_TIMEOUT="30.0"

# Storage Configuration
export AI_DB_DATA_DIR="data"

# Validation Configuration
export AI_DB_STRICT_VALIDATION="true"
export AI_DB_SANDBOX_EXECUTION="true"

# Logging Configuration
export AI_DB_LOG_LEVEL="INFO"
export AI_DB_LOG_AI="false"
```

## Query Language Support

AI-DB understands queries in multiple formats:

### Natural Language
```python
"Show me all users who signed up this month"
"Create a products table with name, price, and description"
"Update John's email to john.doe@example.com"
```

### SQL
```python
"SELECT * FROM users WHERE created_at > '2024-01-01'"
"CREATE TABLE products (id INT PRIMARY KEY, name TEXT)"
"INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')"
```

### Programming Languages
```python
# Python
"[u for u in users if u['is_active']]"

# C# LINQ
"from u in users where u.IsActive select u"

# JavaScript
"users.filter(u => u.isActive).map(u => ({name: u.name, email: u.email}))"
```

## Storage Format

Data is stored in YAML files:

### Table Data
`tables/users.yaml`:
```yaml
- id: 1
  name: Alice
  email: alice@example.com
  is_active: true
- id: 2
  name: Bob
  email: bob@example.com
  is_active: false
```

### Schema
`schemas/users.schema.yaml`:
```yaml
name: users
description: User accounts table
columns:
  - name: id
    type: integer
    nullable: false
    description: User ID
  - name: name
    type: string
    nullable: false
    description: User name
  - name: email
    type: string
    nullable: false
    description: Email address
constraints:
  - name: pk_users
    type: primary_key
    columns: [id]
  - name: uk_email
    type: unique
    columns: [email]
```

### Views
`views/active_users.py`:
```python
def query_active_users(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", False)]
```

## Error Handling

AI-DB provides specific exception types:

```python
from ai_db.exceptions import (
    AIDBError,              # Base exception
    PermissionError,        # Insufficient permissions
    SchemaError,           # Schema-related errors
    ValidationError,       # Data validation failures
    ConstraintViolationError,  # Constraint violations
    CompilationError,      # Query compilation failures
    AIError,              # AI service errors
    StorageError,         # Storage layer errors
    TransactionError      # Transaction-related errors
)
```

## Best Practices

1. **Use appropriate permissions**: Only request the minimum permission level needed
2. **Compile frequently-used queries**: Use compiled queries for better performance
3. **Handle errors gracefully**: Check `result.status` and handle errors appropriately
4. **Provide context**: Pass QueryContext with schema for better AI interpretation
5. **Use transactions**: Always execute queries within a git-layer transaction
6. **Validate data**: AI-DB automatically validates data, but you can add application-level validation too