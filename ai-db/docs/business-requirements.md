# AI-DB Core Engine - Business Requirements

## Overview
AI-DB is a Python library functioning as a database engine where all operations are interpreted and executed by AI. The library executes database operations through natural language input while maintaining data integrity through schema validation.

All operations are provided in natural language in any format - SQL, other query languages, Python, or any other language or metalanguage. AI serves as the sole interpreter for all inputs.

The library provides no chat or dialog interaction - it operates at a similar level to SQLite, with standard and predictable library interfaces. However, internally the AI engine is proactive, able to recover from errors and make decisions based on validation messages.

## Core Requirements

### 1. Operation Types
- **Schema Modification**: Modify table schemas, manage relationships, constraints
- **Data Modification**: Insert, update, delete operations
- **Select Queries**: Complex queries with joins and aggregations
- **View Management**: Create and modify views

### 2. Query Permission Levels
Operations must specify permission level to prevent unintended actions:
- `select` - Read-only queries
- `data_modify` - Data modifications
- `schema_modify` - Schema changes
- `view_modify` - View management

### 3. Response Format
Operations return:
- **Status**: success or failure
- **Data**: Query results (for select operations)
- **Schema**: Result schema (for queries returning data)
- **Data Loss Indicator**: none, probable, or yes
- **AI Comment**: Interpretation details
- **Compiled Plan**: Serialized query plan (for data-returning queries)
- **Transaction ID**: When operating within a transaction

### 4. Query Compilation
- Select queries and views compile to Python
- Compiled plans are serializable strings
- Separate method executes compiled plans without AI
- Compiled queries avoid AI processing overhead

### 5. Schema Features
- Check constraints supported
- Foreign key constraints supported
- Constraints validated through AI-generated Python functions
- All data validated against YAML-stored schemas
- Strongly-typed schema methods
- Schema versioning support
- AI-generated documentation with semantic explanations
- Schema responses include contextual explanations

### 6. Transaction Support
- BEGIN, COMMIT, ROLLBACK operations
- Transactions handled by git-layer library
- AI-DB performs file operations without transaction concerns
- Single-threaded operation

### 7. Storage
- YAML files for data and schema storage
- Documentation files with semantic explanations
- Git-friendly format
- Human-readable structure

## Out of Scope
- Multi-threading support
- Cascade deletion actions