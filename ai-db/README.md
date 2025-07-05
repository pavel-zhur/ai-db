# AI-DB

An AI-native database engine that interprets natural language queries and manages data through AI-powered operations.

## Features

- Natural language query processing (SQL, Python, or any language)
- AI-managed schema modifications and migrations
- Git-based storage with YAML files
- Query compilation to Python for performance
- Strong typing with JSON Schema validation
- Transaction support via git-layer integration
- Comprehensive constraint system with AI-generated validators

## Installation

```bash
pip install ai-db
```

## Configuration

Set your OpenAI-compatible API endpoint and key:

```bash
export AI_DB_API_BASE="https://api.openai.com/v1"
export AI_DB_API_KEY="your-api-key"
export AI_DB_MODEL="gpt-4"
```

## Quick Start

```python
from ai_db import AIDB, PermissionLevel
from git_layer import GitTransaction

# Initialize with git transaction
async with GitTransaction() as transaction:
    db = AIDB()
    
    # Create a table
    result = await db.execute(
        "Create a users table with id, name, email, and created_at fields",
        permissions=PermissionLevel.SCHEMA_MODIFY,
        transaction=transaction
    )
    
    # Insert data
    result = await db.execute(
        "Add user John Doe with email john@example.com",
        permissions=PermissionLevel.DATA_MODIFY,
        transaction=transaction
    )
    
    # Query data
    result = await db.execute(
        "SELECT * FROM users WHERE email LIKE '%example.com'",
        permissions=PermissionLevel.SELECT,
        transaction=transaction
    )
    print(result.data)
```

## Architecture

AI-DB uses AI as the core database engine, not just as a translation layer. The AI:
- Interprets queries in any language or format
- Generates Python code for SELECT queries
- Manages schema evolution and migrations
- Validates data integrity through constraints
- Provides semantic documentation for all operations

## License

MIT