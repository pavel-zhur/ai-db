# AI-DB Phase 1 Inconsistencies Report

After reviewing the documentation from all five projects (AI-DB, Console, MCP, AI-Frontend, Git-Layer), here are the identified inconsistencies and integration issues:

## 1. Transaction Context Interface Mismatch

### Issue
Different projects have different assumptions about the `TransactionContext` interface:

- **AI-DB** expects:
  ```python
  class TransactionContext:
      transaction_id: str
      working_directory: str
      is_write_escalated: bool
      def escalate_write(self) -> str  # Returns new directory
  ```

- **Git-Layer** provides:
  ```python
  class Transaction:
      id: str
      path: str  # Not "working_directory"
      write_escalation_required()  # Different method name
      operation_complete(message: str)  # Not mentioned in AI-DB
  ```

- **MCP Server** assumes transaction context is `Optional[Any]` - no clear interface

### Resolution Needed
Standardize the transaction context interface across all projects.

## 2. Permission Level Naming Inconsistency

### Issue
- **AI-DB** uses enum values: `"select"`, `"data_modify"`, `"schema_modify"`, `"view_modify"`
- **Console** sometimes uses uppercase in comments: `"SELECT"`, `"DATA_MODIFY"`
- **MCP Server** infers permissions but doesn't document exact mapping

### Resolution Needed
Confirm case sensitivity and exact string values for permissions.

## 3. Schema Format Discrepancies

### Issue
AI-DB and AI-Frontend have different schema format expectations:

- **AI-DB** stores schemas as:
  ```yaml
  name: users
  columns:
    - name: id
      type: integer  # Simple type names
  ```

- **AI-Frontend** expects:
  ```python
  {
    "tables": {
      "table_name": {
        "columns": {
          "column_name": {  # Nested structure
            "type": "string|number|integer|boolean"
          }
        }
      }
    }
  }
  ```

### Resolution Needed
Define canonical schema format for inter-service communication.

## 4. Async/Sync Mismatch

### Issue
- **AI-DB**: Fully async (`async def execute()`)
- **Git-Layer**: Fully synchronous (no async support)
- **Console**: Uses async for AI-DB but needs to bridge sync Git-Layer
- **AI-Frontend**: Async but calls sync Git operations

### Resolution Needed
Clarify async/sync bridging strategy, especially for Git-Layer integration.

## 5. API Endpoint Assumptions

### Issue
- **AI-Frontend** assumes AI-DB exposes HTTP API endpoints:
  ```
  POST /api/query
  POST /api/execute
  ```
- **AI-DB** is implemented as a library, not a service
- **Console** uses AI-DB as a library, not via HTTP

### Resolution Needed
Clarify if AI-DB should have an HTTP API server component.

## 6. Configuration Management

### Issue
Different configuration approaches:

- **AI-DB**: Environment variables with `AI_DB_` prefix
- **Console**: YAML config file + environment variables
- **MCP**: Environment variables but different prefix structure
- **Git-Layer**: No configuration, only parameters

### Resolution Needed
Standardize configuration approach and environment variable naming.

## 7. Error Handling Inconsistencies

### Issue
- **AI-DB**: Returns `QueryResult` with `status: bool` and `error: Optional[str]`
- **Console**: Expects exceptions and handles them
- **MCP**: Returns MCP TextContent with `isError: true`
- **Git-Layer**: Raises exceptions

### Resolution Needed
Standardize error handling - exceptions vs result objects.

## 8. File Path References

### Issue
- **Git-Layer** provides `transaction.path`
- **AI-DB** expects `transaction_context.working_directory`
- **Console** uses `transaction.path`

### Resolution Needed
Standardize property naming across interfaces.

## 9. Claude Code Integration

### Issue
- **AI-Frontend** assumes Claude Code CLI is installed and in PATH
- **Console** references `claude_code_path` configuration
- No validation or error handling for missing Claude Code

### Resolution Needed
Define Claude Code CLI discovery and validation strategy.

## 10. Transaction Lifecycle

### Issue
- **Git-Layer** has `operation_complete()` for per-operation commits
- **AI-DB** doesn't mention calling this method
- **Console** doesn't show awareness of per-operation commits

### Resolution Needed
Clarify when and how `operation_complete()` should be called.

## 11. View Storage Format

### Issue
- **AI-DB** stores views as Python files: `views/{name}.py`
- **AI-Frontend** expects views in schema but doesn't specify format
- **MCP** has `view_modify` tool but unclear on view retrieval

### Resolution Needed
Standardize view definition and retrieval format.

## 12. Missing Integration Details

### Issue
Several integration points are undefined:

- How does AI-Frontend get the current schema from AI-DB?
- How does Console handle compiled query plans?
- How does MCP Server get Git-Layer transaction contexts?
- How are transaction IDs generated and shared?

### Resolution Needed
Document complete integration flows between services.

## Recommendations for Supervisor

1. **Create Interface Definitions**: Define canonical interfaces for `TransactionContext`, `Schema`, and `QueryResult` that all services must implement.

2. **Standardize Naming**: Create a naming convention document for:
   - Property names (path vs working_directory)
   - Method names (escalate_write vs write_escalation_required)
   - Permission levels (exact strings and case)

3. **Define Service Boundaries**: Clarify which components are libraries vs services, and whether HTTP APIs are needed.

4. **Async/Sync Strategy**: Document how to bridge async and sync code, especially for Git-Layer integration.

5. **Configuration Unification**: Create a single configuration strategy that all services follow.

6. **Integration Test Suite**: Create integration tests that verify all services work together correctly.

7. **Error Handling Policy**: Decide on exceptions vs result objects as the standard approach.

8. **Documentation Updates**: Each service should update their docs to reflect the standardized interfaces.