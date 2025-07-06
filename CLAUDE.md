# Python Code Guidelines for this project

This document outlines Python-specific coding standards for this project.

## Type System
- Use explicit type annotations everywhere (parameters, return types, variables)
- Follow strict mypy configuration - no Any except where necessary
- Mark non-public members (methods, properties, fields) with leading underscore (`_`) and prefer encapsulation with non-public members over public exposure
- Prefer avoiding union types. Prefer code to work with a single concrete type in each context through proper type narrowing, better conditional handling, or appropriate design patterns.
- Trust the type system - avoid excessive defensive programming or unnecessary null checks. Let errors propagate naturally where appropriate.

## Design Patterns
- Follow best practices for production-ready python libraries and utilities design
- Use dataclasses for data containers with proper field typing
- Try to avoid optional parameters, default values, fallback logic
- Use explicit exception handling with proper types

## Best Practices
- Design for testability with clear dependency boundaries
- Use strongly typed configuration classes
- Don't catch exceptions just to log and re-raise them - let exceptions propagate to appropriate boundary layers where they can be properly handled and logged
- Avoid defensive programming patterns when the type system already guarantees correctness
- Trust the contract provided by interfaces and models - don't add unnecessary checks for conditions that can't occur if the types are correct

## Behavior

- Please don't do workarounds, do only best practices, and if something at hand doesn't work - analyze the reason, fix the root problem, or talk to me and let me decide.

## Code Cleanup Principle

**Remove obsolete code immediately**: If code is no longer needed, no longer functional, or has been superseded by a new implementation, it must be removed completely. Do not leave dead code, unused tests, deprecated functions, or obsolete files in the codebase.

**Examples of code that must be removed:**
- Tests for APIs that no longer exist
- Deprecated functions or classes that have been replaced
- Unused imports, variables, or configuration files
- Old implementation files when new ones replace them
- Comments referring to removed functionality

# Tests strategy

## Tests Logic

- Tests should test the behavior, not the implementation details.
## Test-Production Separation

**Production code must never contain test-specific logic**: No test-related conditionals, imports, or workarounds in production code. Design for testability through dependency injection and clean interfaces, but keep test concerns completely separate from production logic.

# Exception Handling Guidelines

## Core Principle
Let exceptions propagate to where they can be meaningfully handled. Trust your code - avoid defensive programming.

## Simple Decision Framework

- Ask: "Can I recover from this exception?"
- Ask: "Does my caller naturally expect this exception?"
- Ask: "Does my caller need to behave differently based on this exception?"
- Ask: "How much functionality should be canceled?"

## When NOT to Catch

- If you cannot recover AND your caller naturally expects this exception → Let it propagate
- Don't catch just to log and re-raise
- Don't catch for "safety" that returns None/False/empty values
- Don't catch if caller needs this exception for control flow
- Don't catch if exception should cancel more than your operation

## When TO Catch

- You can recover (retry, fallback, fix the issue)
- Background processes that must stay alive
- Exception can be converted to result and caller behaves exactly the same

## Logging

- `ERROR`: Unexpected failures
- `WARN`: Expected but notable conditions
- `INFO`: Normal operational events

# Development Commands

Poetry is pre-installed in the devcontainer. When working on any component in this monorepo, use Poetry for all Python operations:

```bash
# Navigate to the component directory first
cd ai-db  # or ai-shared, ai-frontend, git-layer, console, mcp, ai-hub

# Install component dependencies (creates isolated virtual environment)
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run mypy .
poetry run ruff check .
poetry run black --check .

# Format code
poetry run black .
poetry run ruff check --fix .

# Run component directly
poetry run python -m ai_db  # or relevant module name
```

Never install packages globally. Always use `poetry run` to ensure you're using the correct environment for each component.