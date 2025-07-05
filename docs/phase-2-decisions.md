# Phase 2 Integration Decisions

This document captures all architectural decisions and implementation requirements for the AI-DB system. It describes the target state of the integrated system.

**Note**: This document is derived from phase-2-technical-qa.md. Refer to that document for detailed context and discussions behind these decisions.

## System Architecture

### Component Types

**Libraries:**
- ai-db - SQLite-like library for AI-native database operations
- ai-frontend - Library for generating and managing static frontends
- git-layer - Transaction management library using Git

**Applications:**
- console - CLI for interactive database management
- ai-db-mcp - MCP server exposing AI-DB functionality
- ai-frontend-mcp - MCP server exposing AI-Frontend functionality
- ai-hub - HTTP API server for frontend communication

**Infrastructure:**
- nginx container - Hosts generated static frontends

### Deployment Model

- Libraries run embedded in host applications
- Applications run as separate processes
- Console and MCP servers are completely independent
- Single-tenant deployment for POC
- Multi-tenancy achieved through multiple instances with different configs

## Library Architecture

### ai-db Library

- Operates like SQLite - embedded database engine
- Requires transaction context from caller
- Single operation per method call
- Works with folder path provided by transaction
- No direct Git dependency
- Testable with mock transactions (plain folders)
- Can be used with or without ai-frontend
- Does not clean up files on failure (git-layer handles this)
- Validates data before saving

### ai-frontend Library

- Similar usage pattern to ai-db
- Generates static React/TypeScript frontends
- Works within transaction context
- Stores all generated files in its folder
- No direct file access to ai-db folders
- Stores schema, models, skeleton, Claude Code files, compiled files (schema=DB schema copy, models=TypeScript interfaces, skeleton=React app structure, Claude Code files=generated components, compiled files=built JS/CSS)
- Does not maintain context between calls

### git-layer Library

- Provides transaction context to other libraries
- All async operations
- No dependencies on other libraries
- Handles file versioning and rollback
- Transaction isolation through temporary folders (yes, working folders are clones of the main repo in temporary locations)
- ai-db/ai-frontend notify git-layer of operation success/failure via transaction methods
- On success: git-layer commits to transaction branch
- On failure: creates new branch with -failure suffix, commits, pushes, switches back to transaction branch
- Transaction commit: merges to main and pushes; rollback: creates -rollback branch
- Caught errors within transaction allow continuation; uncaught errors trigger automatic rollback

- Handles DB/frontend uniformly with minimal knowledge of type
- Supports cleanup operations for frontend/DB files (without any logic differences)
- Can work with folder on disk or remote git server

## Configuration Standards

### Libraries (ai-db, ai-frontend, git-layer)
- Use pydantic BaseSettings
- Environment variables with defaults
- Type validation
- .env file support

### Applications (console, mcp, ai-hub)
- Hierarchical configuration
- Environment variables override config files
- Use python-dotenv
- Best practices for each application type

## Transaction Model

### Transaction Flow
1. Use `async with` transaction syntax
2. Read-only by default
3. Call write escalation method when updates needed
4. Each successful operation gets committed
5. Failed operations stay in branch but get cleaned up (creates new -failure branch which is pushed, transaction branch is cleaned up)
6. Rollback keeps branch for debugging (creates -rollback branch and pushes it)
7. Commit merges to main branch (and pushes; all write transactions work in temporary folder clones)

### Transaction Operation Details
- Git assumes read-only unless write mode specified at start
- Write escalation creates temp checkout in new branch
- Path changes to temp path after escalation
- ai-db/ai-frontend call success method for git-layer to commit
- On error, git-layer cleans up working copy but stays in branch (see failure branch creation above)
- On rollback, deletes temp folder but keeps branch history
- Local checkouts for writable transactions
- Permanent main checkout always reflects latest state

### Transaction Properties
- No concurrent write transactions
- Read committed isolation level
- Reads from main branch unless in write transaction
- Simple file lock in `.git/ai-db-write.lock` for write protection
- Lock is per repository, not per branch

### Error Handling
- Failed transactions create branches named `failed-transaction-{timestamp}-{operation}`
- No cleanup of debugging information
- Crashes leave harmless temp folders/branches
- Main branch always stays clean

## Data Model

### Database Structure
- Database = folder of YAML files in Git repository
- Repository structure:
  ```
  repo/
  ├── db/          # AI-DB files
  ├── frontend/    # AI-Frontend files
  └── .git/
  ```
- One database per repository
- Frontend and DB can share repository or use separate ones
- No constraint forcing them together
- git-layer can support multiple DB folders via config parameter (thread-unsafe) (and multiple frontend folders too for uniformity)
- Console uses shared repo pattern as example usage (DB and frontend in same repo, but libraries don't enforce this)
- Frontend is optional until first generation request (DB folder is also optional until first use)

### Schema Format
- JSON Schema standard
- Stored as YAML files for readability
- Passed as Python dicts between components
- TypeScript generation from schemas
- No explicit versioning in POC

### Schema Evolution
- Users modify schemas through natural language
- AI handles all migrations
- Returns success with partial data loss indicator when needed
- Git provides version history

## API Design

### ai-hub API Server
- Separate component from Console
- FastAPI framework
- No WebSockets in POC
- CORS enabled for frontend connections
- OpenAPI documentation
- No health checks or metrics in POC

### API Endpoints (POC)
```
POST /db/query          # Execute compiled queries
POST /db/query/view     # Execute named views  
POST /db/data          # Data modifications (INSERT/UPDATE/DELETE)
```

### API Response Format
- JSON responses for React compatibility
- Input query is free text (could be SQL, LDAP, etc.)
- Read operations return data, plan, and schema (currently only compiled queries supported which return just data; future non-compiled queries will return plan and schema)

- Compiled plan execution has no AI involvement
- Views are compiled plans with semantic info

### Transaction Handling
- Each API call wrapped in implicit transaction
- Immediate commit after each operation
- No transaction state across HTTP requests

## Frontend Architecture

### Generation Process
- ai-frontend uses Claude Code CLI in Docker
- Version pinned for consistency
- No offline operation
- Manual authentication may be required
- Generation errors result in "missing info" or "unresolved questions"
- Console maintains dialog context for retries
- Frontend responds with JSON matching expected schema
- Updates to data via Console/MCP or rigid UI forms

### Storage and Deployment
- Generated code committed to Git
- .gitignore for dist/ and node_modules/ and whatnot (more ignores may be decided during ai-frontend and ai-dc implementation)
- separate .gitignore in ai-frontend that's part of the init, separate in ai-db that's part of the init
- Served by nginx Docker container
- Direct API connection with CORS
- Browser access for user interaction
- Claude Code uses MCP vision tools to see browser screenshots for iterative UI refinement

- Frontend hosting URL not Console's responsibility
- Repository bloat acceptable for POC

### Development Workflow
- Manual F5 refresh for testing
- Include debug symbols in compilation
- TypeScript errors handled by ai-frontend
- No manual fixes - rely 100% on Claude Code
- No hot reload
- Repository can be initialized with seed data from a folder path
- ai-db provides init_from_folder() method that copies and validates YAML schemas
- ai-frontend provides init_from_folder() method that copies and validates TypeScript/React code
- Validation is synchronous, no AI calls - just regular pre-commit validation, i.e. schema validation and TypeScript compilation

### Schema Synchronization
- Manual update when DB schema changes
- Console provides update operation
- Frontend regenerates TypeScript models
- User responsible for keeping in sync
- User provides input during update for Claude Code
- ai-frontend stores DB semantic file alongside its own

## Security Model

### Authentication
- No authentication in POC
- No API keys or JWT tokens
- Completely open access

### Permissions
- AI-DB enforces permission levels during query execution
- Four levels: select, data_modify, schema_modify, view_modify
- Current granularity is sufficient
- No row or column level security

## Error Handling

### Philosophy

**General Error Handling:**
- Fail fast on invalid inputs or configuration errors
- Clear error messages with actionable details
- No silent failures or fallback behaviors

**Library-Specific Behavior:**
- ai-db: Throws exceptions on schema violations, invalid queries, or data integrity issues
- ai-frontend: Throws exceptions on compilation errors, missing dependencies, or invalid schemas
- git-layer: Throws exceptions on merge conflicts, lock acquisition failures, or repository errors
- User-friendly errors with technical details
- Technical details in expandable sections or logs
- ai-db validates returned data adheres to schema
- ai-frontend runs TypeScript compilation, ESLint checks, and validates React component structure
- Best practices per context (MCP, console, libs, TypeScript, UX)
- Follow exception handling guidelines in root CLAUDE.md

### Retry Strategy
- AI operations may retry (configurable)
- ai-db may retry from scratch
- ai-frontend may call Claude Code multiple times
- 5-minute timeout for Claude Code calls
- No circuit breakers in POC

### Progress Feedback
- Print "Still working..." every 30 seconds
- Show connection errors if connection lost

## Testing Strategy

### Test Infrastructure
- Use testcontainers-python for integration tests
- Always mock AI APIs and Claude Code
- Each component has independent tests
- Azure DevOps pipeline for CI/CD
- GitHub Actions workflows for open-source contributors

- Tests must run on host machine, in devcontainer, and in CI/CD
- Keep tests simple
- Integration tests per library (library-local)
- Some integration tests in console and MCP

### Test Isolation
- ai-db and ai-frontend testable without Git
- Mock transactions with plain folders
- No real AI token usage in tests

## Component Communication

### Interface Standards
- git-layer defines TransactionContext interface
- All components depend on git-layer
- No adapters needed - standardize at source
- Use enums for permission levels everywhere
- MCP servers must provide all DB/frontend info including schemas and semantic descriptions
- Console also exposes full schema and semantic information through its commands

- MCP servers are required in POC for Claude/Copilot integration

### Schema Access
- ai-db provides get_schema() method
- ai-frontend consumes schema on init
- No direct file access between components
- Pass schema data through method calls

### Initialization
- Console and MCP independently initialize libraries
- Each creates own instances with configs
- Follow configuration best practices
- Libraries can be in separate repos
- Libraries auto-initialize empty folders on first use
- ai-db creates initial schema files when db/ folder is empty
- ai-frontend creates initial project structure when frontend/ folder is empty
- git-layer only creates empty folders and provides paths via transaction context

- User provides path to repo in config

## Operational Requirements

### Logging
- Console writes session log file
- Python logger output saved to .log files (structured logging)
- Human-readable session transcript saved as .md file with timestamps

- Standard logging across components
- No metrics or monitoring in POC
- Git history provides audit trail

### Performance
- No specific targets for POC
- No caching implementation
- Frontend uses compiled queries only

### High Availability
- Single instance deployment
- No backup/restore strategy
- No disaster recovery

## Component Naming

- Use hyphens in names
- No prefixes for now
- Consistent naming pattern

## Success Criteria

- All tests pass
- Compilation works
- GitHub Actions/Azure DevOps pipelines work
- Docker compose brings up full system
- Console operations work correctly
- MCP servers respond properly
- Frontend displays data and accepts updates
- Correct error handling for invalid requests

## Future Considerations (Not in POC)

- Chat and voice features in ai-hub
- Frontend regeneration API
- Authentication and authorization
- WebSocket support
- Hot reload for development
- Schema versioning
- Concurrent write protection beyond simple lock
- Circuit breakers
- Performance optimization
- High availability features
- Visual designer for managing UIs and web interface for chats
- Chat context storage with LangChain
- Frontend URL knowledge in Console
- AI agent capabilities in ai-hub
- write-escalation permission check (currently permissions are checked / not checked by the ai-db and ai-frontend)