# AI-Frontend Phase 1 Inconsistencies Report

## Overview
This document identifies inconsistencies between AI-Frontend and other services discovered during parallel development, including unresolved questions and integration issues that need supervisor attention for a production-ready system.

## Critical Integration Blockers

### 1. Missing API Server Component
**Issue**: AI-Frontend generates HTTP-based clients, but no HTTP API server exists

**Current Architecture**:
- AI-DB is a Python library with methods like `execute()`, not an HTTP server
- Console integrates directly with AI-DB library via dependency injection
- MCP servers use MCP protocol, not HTTP
- AI-Frontend generates React apps expecting HTTP endpoints

**Generated Frontend Expects**:
```typescript
POST /api/query - {query: string, permission: "select"}
POST /api/execute - {query: string, permission: "data_modify" | "schema_modify"}
```

**AI-DB Actually Provides**:
```python
async def execute(query: str, permission_level: PermissionLevel, transaction_context: TransactionContext) -> QueryResult
```

**Impact**: Generated frontends cannot communicate with backend at all

**Resolution Required**: 
- Create an HTTP API server that wraps AI-DB library
- OR completely redesign frontend generation to not expect HTTP
- Define who owns this API server component

### 2. Transaction Context Incompatibility
**Issue**: AI-Frontend's TransactionContext doesn't match git-layer's Transaction class

**AI-Frontend Expects**:
```python
@dataclass
class TransactionContext:
    transaction_id: str
    working_directory: Path
    commit_message_callback: Optional[callable] = None
```

**Git-Layer Actually Provides**:
```python
class Transaction:
    path: str  # Not Path object
    write_escalation_required() -> None  # AI-Frontend never calls this
    operation_complete(message: str) -> None  # AI-Frontend doesn't use
    checkpoint(message: str) -> None
```

**Impact**: 
- AI-Frontend cannot properly integrate with git-layer transactions
- Write escalation not implemented, violating transaction isolation
- Operation tracking incomplete

### 3. Schema Access Pattern Undefined
**Issue**: How AI-Frontend gets database schema is inconsistent across implementations

**Current Situation**:
- AI-Frontend expects schema passed as parameter
- Console would need to fetch schema via AI-DB and pass it
- But Console's implementation doesn't show this integration
- AI-DB stores schemas in YAML, provides them via `get_schema()`

**Questions**:
- Should Console fetch and pass schema to AI-Frontend?
- Should AI-Frontend have direct access to AI-DB for schema?
- What happens when schema changes during a transaction?

### 4. Permission Level Case Sensitivity
**Issue**: Permission level strings may have case mismatches

**AI-Frontend Uses** (lowercase):
- "select", "data_modify", "schema_modify"

**AI-DB PermissionLevel Enum** (from implementation):
- Likely uppercase: SELECT, DATA_MODIFY, SCHEMA_MODIFY

**Impact**: API calls will fail with invalid permission errors

### 5. No Console ↔ AI-Frontend Interface Documented
**Issue**: Console mentions AI-Frontend integration but provides no interface details

**Console's phase-1-implementation says**:
- "Integrates with AI-Frontend (interface assumed similar to AI-DB)"
- No actual code showing how it calls AI-Frontend

**AI-Frontend Provides**:
```python
async def generate_frontend(request: str, schema: Dict, transaction_context: TransactionContext) -> GenerationResult
async def update_frontend(request: str, schema: Dict, transaction_context: TransactionContext) -> GenerationResult
```

**Missing Details**:
- How Console determines when to call AI-Frontend
- How Console passes schema from AI-DB to AI-Frontend
- How Console handles GenerationResult

### 6. Compiled Query Support Missing in Frontend
**Issue**: AI-DB supports compiled queries for performance, but frontend doesn't

**AI-DB Provides**:
- `execute_compiled(compiled_plan: str, ...)` for performance
- Returns compiled plans in QueryResult

**AI-Frontend Generated Code**:
- Only supports text queries
- No way to store or execute compiled plans
- Performance optimization unavailable

### 7. Error Response Format Mismatch
**Issue**: Frontend expects different error format than backend provides

**Frontend Expects**:
```typescript
{
  success: boolean;
  error?: string;
  message?: string;
}
```

**AI-DB QueryResult Contains**:
```python
{
  "success": bool,
  "data": Any,
  "error": Optional[str],
  "data_loss_indicator": str,  # Frontend doesn't handle
  "ai_comment": str,           # Frontend ignores
  "compiled_plan": Optional[str],
  "transaction_id": Optional[str]
}
```

### 8. Chrome MCP Integration Not Implemented
**Issue**: Configuration exists but no implementation

**Current State**:
- Config has `enable_chrome_mcp` and `chrome_mcp_port`
- No actual Chrome integration code
- Puppeteer MCP or Microsoft MCP mentioned but not used

**Impact**: Visual feedback feature completely non-functional

## My Unresolved Questions (AI-Frontend)

1. **Authentication/Authorization**: No auth mechanism specified - how will production frontends authenticate with the API server?

2. **Multi-tenant Support**: Can one frontend connect to multiple AI-DB instances? How to handle different schemas?

3. **Schema Migration**: When AI-DB schema changes, how do we migrate existing deployed frontends?

4. **Deployment Strategy**: How will generated frontends be deployed? Docker? CDN? Who handles this?

5. **API Server Ownership**: Who implements the HTTP API server? Is it part of AI-DB, Console, or a separate component?

6. **Real-time Updates**: Should frontends support WebSocket connections for live data updates?

7. **Error Recovery**: What happens if Claude Code CLI isn't available or fails repeatedly?

8. **Caching Strategy**: Should generated components be cached for similar requests?

9. **Monitoring/Telemetry**: Should we add analytics to generated frontends? How to track usage?

10. **Internationalization**: Will i18n be needed? The technical Q&A said "not in POC" but for production?

## Integration Flow Issues

### Expected Flow (Based on My Understanding):
1. User requests UI in Console
2. Console begins git-layer transaction
3. Console fetches schema from AI-DB
4. Console calls AI-Frontend with schema and transaction
5. AI-Frontend generates React app in transaction directory
6. Generated app needs HTTP API to talk to AI-DB
7. Console commits transaction

### Problems with This Flow:
- Step 6 fails - no HTTP API exists
- Step 3-4 not implemented in Console
- Transaction context incompatible between steps

## Recommendations for Supervisor

### 1. Define API Server Component
- **Option A**: Add HTTP server to AI-DB package
- **Option B**: Create separate API service package
- **Option C**: Redesign frontend to use different communication method

### 2. Standardize Transaction Context
Create adapter or standardize interface:
```python
class UnifiedTransactionContext:
    id: str
    working_directory: Path
    git_transaction: git_layer.Transaction  # Original object
    
    def write_escalation_required(self):
        self.git_transaction.write_escalation_required()
```

### 3. Define Schema Distribution Strategy
- **Option A**: Console acts as orchestrator, fetches and distributes schema
- **Option B**: AI-Frontend gets direct read access to AI-DB
- **Option C**: Schema served by the (missing) API server

### 4. Create Integration Test Suite
Must test end-to-end:
- Console → Git-Layer → AI-DB → Data changes
- Console → Git-Layer → AI-Frontend → Generated UI
- Generated UI → API Server → AI-DB → Response
- Transaction commit/rollback across all components

### 5. Document Missing Interfaces
- Console ↔ AI-Frontend integration
- HTTP API specification
- Deployment procedures
- Error handling standards

## Additional Context for Supervisor

### Component Maturity Levels:
- **Git-Layer**: Most complete, clear interface ✓
- **AI-DB**: Core complete, missing HTTP layer ⚠️
- **MCP**: Complete for MCP protocol, not for HTTP ✓
- **Console**: Integration points undefined ⚠️
- **AI-Frontend**: Complete but incompatible assumptions ❌

### Critical Path for Production:
1. Implement HTTP API server (blocks everything)
2. Fix transaction context compatibility
3. Implement Console integrations
4. Add authentication/authorization
5. Define deployment strategy
6. Create integration tests

### Suggested Component Ownership:
- **API Server**: Should be separate package or part of AI-DB
- **Schema Management**: AI-DB should own, others consume
- **Transaction Orchestration**: Console should coordinate
- **Deployment**: Needs dedicated tooling/service

The system architecture is sound but needs these integration pieces to function as a production system.