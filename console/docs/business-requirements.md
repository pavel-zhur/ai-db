# AI-DB Console - Business Requirements

## Overview
A console application providing a simple chat interface for AI-DB and AI-Frontend. Maintains dialogue history and calls appropriate library functions when needed.

## Core Requirements

### 1. Chat Interface
- Maintains conversation history
- Natural language input/output
- No special command syntax required

### 2. Context Management
- Remembers previous queries and results
- Allows references to previous operations
- Maintains session state

### 3. AI-DB Integration
- Calls appropriate AI-DB functions based on user input
- Automatically determines permission levels
- Passes context from conversation to queries

### 4. AI-Frontend Integration
- Calls AI-Frontend functions for UI-related requests
- Passes schema context from AI-DB to AI-Frontend
- Manages frontend generation and updates

### 5. Result Display
- Formats query results as tables
- Shows operation status and messages
- Displays AI interpretation comments

### 6. Transaction Management
- Begin/commit/rollback for AI-DB operations
- Begin/commit/rollback for AI-Frontend operations
- Shows transaction status
- Allows preview before commit

### 7. Safety Features
- Confirms destructive operations
- Shows data loss indicators

## Out of Scope
- Voice input
- Web interface
- Multiple database connections