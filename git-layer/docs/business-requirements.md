# Git-Layer - Business Requirements

## Overview
Git-Layer is a Python library that implements database-style transactions using Git as the underlying engine. Provides BEGIN, COMMIT, and ROLLBACK operations for file-based systems.

## Core Requirements

### 1. Transaction Operations
- **BEGIN**: Create a new Git branch for the transaction
- **COMMIT**: Merge changes back to main branch
- **ROLLBACK**: Discard branch and restore original state

### 2. File Operations
- All file changes happen within transaction context
- No direct Git interaction required by client libraries
- Transparent operation for ai-db and ai-frontend

### 3. Integration
- Simple API for ai-db and ai-frontend to use
- No Git knowledge required by consuming libraries
- Handle all Git operations internally

### 4. Safety
- Atomic operations (all or nothing)
- Prevent conflicts in single-threaded environment
- Clean up abandoned transactions

### 5. Simplicity
- Minimal API surface
- No configuration required
- Works with existing Git repositories

## Architecture
The library wraps Git operations to provide transaction semantics. Client libraries (ai-db, ai-frontend) perform normal file operations, and git-layer handles the version control aspects transparently.

## Out of Scope
- Multi-threading support
- Distributed transactions
- Transaction isolation levels
- Conflict resolution (single-threaded assumption)