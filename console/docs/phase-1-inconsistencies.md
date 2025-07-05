# Phase 1 Inconsistencies Report - Console

## Overview

This document identifies inconsistencies found across the five parallel implementations (AI-DB, AI-Frontend, Git-Layer, MCP Server, and Console) that need to be resolved for proper system integration.

## Critical Inconsistencies

### 1. Missing API Server Component

**Issue**: AI-Frontend expects an HTTP API server but none exists.

**Details**:
- AI-Frontend is configured to call API endpoints (POST /api/query, POST /api/execute)
- AI-DB is implemented as a library, not a server
- MCP Server provides MCP protocol tools, not HTTP endpoints
- No project is responsible for creating the HTTP API bridge

**Impact**: AI-Frontend cannot communicate with AI-DB in production.

**Recommendation**: Need a new component "ai-db-api-server" that:
- Wraps AI-DB library
- Exposes HTTP endpoints
- Handles transaction management
- Manages AI-DB lifecycle

### 2. Transaction Context Interface Mismatch

**Issue**: Different transaction context interfaces across projects.

**AI-DB expects**:
```python
class TransactionContext:
    transaction_id: str
    working_directory: str  # String type
    is_write_escalated: bool = False
    def escalate_write(self) -> str: ...
```

**AI-Frontend expects**:
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path  # Path type
    commit_message_callback: Optional[callable] = None
```

**Git-Layer provides**:
- `path` property (not `working_directory`)
- `write_escalation_required()` method (not `escalate_write()`)
- `operation_complete(message)` for intermediate commits

**Console uses**:
- Direct GitTransaction from git-layer
- No abstraction layer

**Impact**: Components cannot share transaction contexts.

**Recommendation**: Standardize on Git-Layer's actual interface or create adapter classes.

### 3. Schema Format Incompatibility

**Issue**: AI-DB and AI-Frontend use different schema formats.

**AI-DB schema format** (YAML):
```yaml
name: users
columns:
  - name: id
    type: integer
    nullable: false
```

**AI-Frontend expects** (JSON Schema):
```json
{
  "tables": {
    "users": {
      "columns": {
        "id": {
          "type": "integer",
          "required": true
        }
      }
    }
  }
}
```

**Impact**: Schema cannot be passed directly from AI-DB to AI-Frontend.

**Recommendation**: AI-DB should provide schema in JSON Schema format or add a converter.

### 4. Permission Level Handling Ambiguity

**Issue**: Inconsistent permission level handling.

**Current State**:
- AI-DB requires explicit PermissionLevel enum in execute()
- MCP Server is told to "infer" permissions from operations
- Console maps command types to permissions

**Impact**: MCP tools might infer permissions incorrectly.

**Recommendation**: MCP Server should use the same mapping logic as Console.

### 5. Async/Sync Integration Issues

**Issue**: Mixed async/sync patterns.

**Current State**:
- AI-DB is fully async
- AI-Frontend is fully async
- Git-Layer examples show sync context manager
- Console uses async with Git-Layer (but Git-Layer examples are sync)

**Impact**: Unclear if Git-Layer actually supports async.

**Recommendation**: Verify Git-Layer's async support or add async wrappers.

### 6. File Path Inconsistencies

**Issue**: Different file organization documented.

**AI-DB phase-1-implementation.md** shows:
- data/schemas/{table}.schema.yaml
- data/tables/{table}.yaml
- data/views/{view}.py

**AI-DB API.md** shows:
- schemas/{table}.schema.yaml (no data/ prefix)

**Impact**: Confusion about actual file structure.

**Recommendation**: Standardize and document the exact structure.

### 7. Configuration Management Chaos

**Issue**: No unified configuration approach.

**Current State**:
- Each project has different config mechanisms
- Environment variable names not coordinated
- Some use Pydantic, others use dictionaries
- MCP Server configuration approach unclear

**Impact**: Difficult to configure the full system.

**Recommendation**: Create a unified configuration schema.

### 8. Chrome MCP Integration Confusion

**Issue**: Chrome MCP mentioned but not integrated.

**Details**:
- AI-Frontend technical Q&A mentions Chrome MCP
- MCP Server says visual features are "irrelevant"
- No actual Chrome MCP integration exists

**Impact**: Expected feature missing.

**Recommendation**: Clarify if Chrome MCP is needed for phase 1.

### 9. Operation Completion Tracking

**Issue**: Git-Layer expects operation tracking but it's not used.

**Git-Layer provides**: `operation_complete(message)` for each operation
**Other projects**: Don't call this method

**Impact**: Transaction branches might not have granular commits.

**Recommendation**: Decide if granular commits are needed.

### 10. Error Handling Philosophy

**Issue**: Different retry limits and strategies.

**Current State**:
- AI-DB: 3 retry attempts
- AI-Frontend: 5 iterations max
- Different timeout values
- Inconsistent error recovery approaches

**Impact**: Unpredictable behavior under failure.

**Recommendation**: Standardize retry policies.

## Integration Gaps

### 1. No Compiled Query Execution in MCP

MCP Server doesn't expose the compiled query execution tool that AI-DB provides.

### 2. Semantic Documentation Location

Multiple mentions of "semantic docs" but no standard location or format defined.

### 3. Transaction Message Sources

Git-Layer expects commit messages but it's unclear who provides them:
- AI-DB might provide them
- Console currently uses generic messages
- AI-Frontend doesn't specify

## Console-Specific Issues

### 1. Direct Library Dependencies

Console imports ai-db, ai-frontend, and git-layer directly, assuming they're pip-installable. The Docker build assumes local file paths.

### 2. No API Server Integration

Console creates AI-DB instances directly rather than using an API server (which doesn't exist).

### 3. Frontend Path Handling

Console reports frontend output paths but doesn't handle the static file serving aspect.

## Recommendations for Supervisor

1. **Create AI-DB API Server**: New component to bridge AI-DB library to HTTP
2. **Standardize Interfaces**: Create interface definitions all projects must follow
3. **Unify Configuration**: Single configuration schema for the entire system
4. **Clarify Git-Layer Async**: Determine if async support exists or needs adding
5. **Resolve Schema Format**: Pick one format and stick to it
6. **Document File Structure**: Create canonical file structure documentation
7. **Integration Tests**: Need integration tests to catch these issues
8. **API Documentation**: Create OpenAPI specs for all HTTP interfaces

## Priority Order

1. **Critical**: Missing API server (blocks AI-Frontend)
2. **High**: Transaction context interface mismatch
3. **High**: Schema format incompatibility
4. **Medium**: Configuration management
5. **Medium**: Async/sync clarity
6. **Low**: Chrome MCP integration
7. **Low**: Semantic documentation standards