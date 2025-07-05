# AI-Frontend Architecture

## Overview

AI-Frontend is a Python library that generates React frontends using Claude Code CLI as the generation engine. It integrates with AI-DB schemas to create type-safe, Material-UI based applications.

## Core Components

### 1. AiFrontend (core.py)
The main orchestrator that coordinates the generation process:
- Manages the overall workflow
- Handles transaction contexts from git-layer
- Coordinates between different generators

### 2. ClaudeCodeWrapper (claude_integration.py)
Wraps Claude Code CLI for programmatic use:
- Builds prompts with proper context
- Manages iterative generation
- Handles Claude Code subprocess execution
- Monitors completion status

### 3. SkeletonGenerator (skeleton_generator.py)
Creates the base React project structure:
- Vite configuration
- TypeScript setup
- Material-UI integration
- Basic project scaffolding

### 4. TypeScriptGenerator (type_generator.py)
Converts AI-DB schemas to TypeScript types:
- JSON Schema to TypeScript conversion
- Interface generation for tables and views
- DTO types for create/update operations
- API response types

### 5. ApiGenerator (api_generator.py)
Creates API client code:
- Service functions for CRUD operations
- React hooks for data fetching
- Retry logic implementation
- Type-safe API calls

### 6. FrontendCompiler (compiler.py)
Validates generated code:
- npm dependency installation
- TypeScript compilation
- Build process execution
- Error extraction and reporting

## Generation Flow

1. **Initialize**: Create React skeleton with all necessary configuration
2. **Generate Types**: Convert AI-DB schema to TypeScript interfaces
3. **Create API Layer**: Generate service functions and hooks
4. **Invoke Claude**: Use Claude Code CLI to generate UI components
5. **Iterate**: Let Claude refine until SEMANTIC_DOCS.md indicates completion
6. **Compile**: Validate the generated code compiles successfully
7. **Fix Errors**: If compilation fails, give Claude one more chance to fix

## Integration Points

### Git-Layer Integration
- Receives transaction context with working directory
- All file operations happen within transaction directory
- Supports commit message callbacks
- Single-threaded operation assumption

### AI-DB Schema Integration
- Reads JSON Schema formatted database schemas
- Generates corresponding TypeScript types
- Creates API calls matching schema structure
- Supports foreign keys and constraints

### Claude Code CLI Integration
- Subprocess execution with proper isolation
- Context file provision via temporary directories
- Iterative refinement support
- Chrome MCP integration for visual feedback

## Configuration

The library is configured via `AiFrontendConfig`:
- Claude Code CLI settings (path, args, timeout)
- Build preferences (Material-UI, Vite, TypeScript)
- API configuration (base URL, retry settings)
- Chrome MCP settings (enable/disable, port)

## Error Handling

Multiple levels of error handling:
1. **Generation Errors**: When Claude fails to generate
2. **Compilation Errors**: When TypeScript or build fails
3. **Transaction Errors**: When git-layer operations fail
4. **Configuration Errors**: When required tools are missing

## Security Considerations

- Claude Code runs with restricted command line arguments
- Generated code is validated through compilation
- No direct execution of untrusted code
- API endpoints are parameterized to prevent injection