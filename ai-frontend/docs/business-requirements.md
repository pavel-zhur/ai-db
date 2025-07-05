# AI-Frontend - Business Requirements

## Overview
AI-Frontend manages React frontends through natural language, analogous to how AI-DB manages data. Uses Claude Code CLI as the generation engine to build and modify UI components and pages.

## Core Requirements

### 1. Frontend Generation
- Build React components from natural language requests
- Modify existing components based on instructions
- Generate complete pages with layouts
- Include documentation with semantic explanations

### 2. AI-DB Integration
- Schema known at generation/update time
- When schema changes, AI updates frontend components
- Generate TypeScript types from database structure
- Create appropriate data fetching hooks
- Handle loading and error states

### 3. Claude Code Integration
- Use Claude Code CLI as the core engine
- Chrome MCP integration for visual context
- Pass schema context to Claude Code
- Maintain consistent code style
- Generate git-friendly code

### 4. Component Features
- Voice input support (microphone integration)
- Pointing gesture support (click elements while talking)
- Responsive design by default
- Accessibility compliance

### 5. Code Management
- Components stored in organized structure
- Documentation files with semantic explanations
- Maintains design system consistency
- Version control friendly output

### 6. Transaction Support
- BEGIN, COMMIT, ROLLBACK operations
- Transactions handled by git-layer library
- AI-Frontend performs file operations without transaction concerns
- Single-threaded operation

## Architecture
Frontend modifications happen through natural language requests processed by Claude Code CLI. Generated components automatically integrate with AI-DB schemas and include proper TypeScript types and documentation.

## Out of Scope
- Non-React frameworks
- Design tool integrations
- Mobile native applications