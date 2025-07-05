# AI-Frontend Phase 1 Inconsistencies Report

## Overview
This document identifies inconsistencies between AI-Frontend and other services discovered during parallel development. These need supervisor attention for resolution.

## Critical Inconsistencies

### 1. API Endpoint Structure Mismatch
**Issue**: AI-Frontend expects different API endpoints than AI-DB provides

**AI-Frontend expects**:
- POST /api/query (with body: {query, permission: "select"})
- POST /api/execute (with body: {query, permission: "data_modify|schema_modify"})

**AI-DB provides** (per MCP implementation):
- Direct method calls: execute(query, permissions, transaction)
- No HTTP API server implementation mentioned

**Impact**: Generated frontends cannot communicate with AI-DB without an API server layer

**Resolution needed**: 
- Either create an API server wrapper for AI-DB
- Or modify AI-Frontend to expect a different API structure

### 2. Transaction Context Interface Discrepancy
**Issue**: Different transaction context structures between services

**AI-Frontend TransactionContext**:
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path
    commit_message_callback: Optional[callable] = None
```

**AI-DB expects** (from phase-1-implementation):
```python
class TransactionContext:
    # Includes additional methods like write_escalation_required()
    # More complex than what AI-Frontend provides
```

**Impact**: AI-Frontend may not provide complete transaction context needed by AI-DB

### 3. Console Integration Interface Unknown
**Issue**: Console's phase-1-implementation mentions AI-Frontend integration but doesn't specify the interface

**Console mentions**:
- "Integrates with AI-Frontend (interface assumed similar to AI-DB)"
- No concrete interface documented

**AI-Frontend provides**:
```python
async def generate_frontend(request: str, schema: Dict, transaction_context: TransactionContext)
async def update_frontend(request: str, schema: Dict, transaction_context: TransactionContext)
```

**Impact**: Console may not know how to properly call AI-Frontend

### 4. Schema Access Pattern Unclear
**Issue**: How AI-Frontend gets the database schema is inconsistent

**AI-Frontend assumes**:
- Schema passed directly as parameter
- JSON Schema format expected

**AI-DB provides**:
- get_schema() method that includes semantic documentation
- Schema stored in YAML files

**Console's role**:
- Unclear if Console fetches schema and passes it, or if AI-Frontend should fetch directly

### 5. Git-Layer Write Escalation Not Implemented
**Issue**: AI-Frontend doesn't use git-layer's write escalation feature

**Git-Layer provides**:
- `transaction.write_escalation_required()` for write operations
- Creates temporary clones for isolation

**AI-Frontend behavior**:
- Assumes it can write directly to working_directory
- No write escalation calls

**Impact**: May violate git-layer's transaction isolation model

### 6. Compiled Query Execution Not Supported
**Issue**: AI-Frontend's generated API client doesn't support compiled queries

**AI-DB provides**:
- Compiled query execution via execute_compiled()
- Returns serialized Python code for performance

**AI-Frontend generates**:
- Only supports text queries via query() method
- No compiled query support in API client

**Impact**: Generated frontends cannot leverage query compilation for performance

### 7. Error Response Format Inconsistency
**Issue**: Different error formats expected vs provided

**AI-Frontend expects**:
```typescript
{
  success: boolean;
  error?: string;
  message?: string;
}
```

**AI-DB QueryResult structure** (from MCP):
```python
{
  "success": bool,
  "data": optional,
  "error": optional,
  "data_loss_indicator": str,
  "ai_comment": str,
  "compiled_plan": optional,
  "transaction_id": optional
}
```

**Impact**: Frontend error handling may not work correctly

### 8. Permission Level Naming Inconsistency
**Issue**: Different permission level names

**AI-Frontend uses**:
- "select", "data_modify", "schema_modify"

**AI-DB uses** (PermissionLevel enum):
- Might be "SELECT", "DATA_MODIFY", "SCHEMA_MODIFY" (uppercase)

**Impact**: API calls may fail due to invalid permission values

### 9. Missing API Server Component
**Issue**: No API server implementation exists between frontend and AI-DB

**Current state**:
- AI-Frontend generates clients expecting HTTP API
- AI-DB is a Python library with no HTTP server
- MCP servers use MCP protocol, not HTTP

**Impact**: Generated frontends cannot connect to backend

### 10. Chrome MCP Integration Details Missing
**Issue**: Chrome MCP integration mentioned but not implemented

**AI-Frontend mentions**:
- Chrome MCP for visual feedback
- Puppeteer MCP or Microsoft MCP

**Actual implementation**:
- No Chrome integration code
- Config has chrome_mcp_port but unused

**Impact**: Visual feedback feature non-functional

## Recommendations for Supervisor

1. **Define standard API contract** between frontend and backend
2. **Create API server component** or modify frontend expectations
3. **Standardize transaction context** across all services
4. **Document Console ↔ AI-Frontend interface** explicitly
5. **Clarify schema passing mechanism** and format
6. **Implement write escalation** in AI-Frontend or clarify if needed
7. **Add compiled query support** to frontend or remove from AI-DB
8. **Align error response formats** across services
9. **Standardize permission level values** (case, format)
10. **Decide on Chrome MCP** implementation or remove references

## Integration Testing Needed

1. End-to-end flow: Console → AI-Frontend → Generated UI → AI-DB API
2. Transaction lifecycle with proper git-layer integration
3. Schema changes propagating to frontend updates
4. Error handling across service boundaries
5. Performance with compiled vs text queries

## Missing Components

1. **API Server**: Bridge between HTTP frontend and Python AI-DB
2. **Schema synchronization**: Mechanism to keep frontend types updated
3. **Development server**: For frontend hot-reload during AI-DB changes
4. **Integration tests**: Cross-service testing framework
5. **Deployment orchestration**: How all services deploy together