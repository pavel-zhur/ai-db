# Phase 2 Standardization Plan

This document provides the comprehensive plan for standardizing the AI-DB system codebase to create a unified, professional, and maintainable project.

## Overview

The current state consists of 5 independently developed components that need to be transformed into a cohesive system. This plan addresses both structural standardization and technical integration to achieve a truly holistic codebase.

## Guiding Principles

1. **Consistency Over Perfection**: Choose one approach and apply it everywhere
2. **Minimal Viable Infrastructure**: Remove redundancy, keep only what's necessary
3. **Developer First**: Optimize for ease of development and contribution
4. **Production Patterns**: Use industry-standard practices even for POC

## Part 1: Repository Structure

### Current State Analysis

Currently we have:
- 5 separate component directories with inconsistent structures
- Mixed approaches to testing (some have tests/, some have test/)
- Inconsistent documentation (some detailed, some minimal)
- Different Python packaging approaches (setup.py vs pyproject.toml)
- Varying Docker strategies (some have Dockerfiles, some don't)
- No shared code or standardized interfaces

### Target Monorepo Structure

```
ai-db-system/
├── .github/
│   └── workflows/
│       ├── ci.yml               # CI workflow for entire system
│       └── publish.yml          # PyPI publishing workflow
├── ai-db/                       # Independent library
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── ai-frontend/                 # Independent library
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── git-layer/                   # Independent library
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── console/                     # Independent application
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── mcp/                        # Independent application
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── ai-hub/                     # Independent application
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── shared/                     # Published as ai-db-shared package
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
├── tests/
│   └── integration/            # Cross-component integration tests
├── docker-compose.yml          # Full system deployment
├── azure-pipelines.yml         # Azure DevOps pipeline
├── Makefile                    # Essential commands only
├── pyproject.toml             # Workspace-level configuration
└── README.md                  # Getting started guide
```

### Component Structure Standard

Each component follows this structure:

```
{component-name}/
├── src/
│   └── {name}/                 # Package name (underscores)
│       ├── __init__.py
│       ├── __version__.py      # Single source of version
│       ├── config.py           # Pydantic settings
│       └── py.typed            # Type checking marker
├── tests/                      # Component tests
│   └── test_*.py              # Test files
├── Dockerfile                  # Component-specific image
├── README.md                  # Component documentation
└── pyproject.toml             # Full package metadata for PyPI
```

## Part 2: Python Standardization

### Single Python Version
- **Python 3.13** for all components (latest stable)

### Workspace Configuration

Each component has its own `pyproject.toml` for independent publishing. The root workspace configuration is minimal:

```toml
# Root pyproject.toml - workspace configuration only
[tool.black]
line-length = 100
target-version = ["py313"]

[tool.ruff]
line-length = 100
target-version = "py313"
select = ["E", "F", "I", "N", "W"]  # Essential rules only

[tool.mypy]
python_version = "3.13"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Component pyproject.toml Template

Each component has a complete `pyproject.toml` for PyPI publishing:

```toml
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "ai-db"  # or ai-frontend, git-layer, etc.
version = "0.1.0"
description = "AI-native database engine"
authors = ["AI-DB Team"]
license = "MIT"
readme = "README.md"
repository = "https://github.com/pavel-zhur/ai-db"
packages = [{include = "ai_db", from = "src"}]

[tool.poetry.dependencies]
python = "^3.13"
ai-shared = "^0.1.0"  # For interfaces (except in ai-shared itself)
# Component-specific dependencies

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
mypy = "^1.8"
ruff = "^0.1"
black = "^24.1"
```

## Part 3: Testing Standardization

### Test Organization

1. **Component Tests** (`{component}/tests/`)
   - Unit and integration tests together
   - Mock external dependencies
   - Test component in isolation

2. **Integration Tests** (`tests/integration/`)
   - Cross-component interactions only
   - Use testcontainers for external services
   - Test actual integration points

### Shared Package Content

The `ai-shared` package contains only interface definitions:
```python
# ai-shared/src/ai_shared/protocols.py
from typing import Protocol
from pathlib import Path

class TransactionProtocol(Protocol):
    """Interface that git-layer implements"""
    @property
    def id(self) -> str: ...
    @property
    def path(self) -> Path: ...
    async def write_escalation_required(self) -> None: ...
    async def operation_complete(self, message: str) -> None: ...
```

### Test Standards

1. **Simple naming**: `test_{feature}_works` or `test_{feature}_fails_when_{condition}`
2. **Minimal mocking**: Mock only at system boundaries
3. **Async everywhere**: Use pytest-asyncio
4. **Practical coverage**: 80% target

## Part 4: Docker Standardization

### Shared Base Image

Common base image for all Python components:

```dockerfile
# docker/base/Dockerfile
FROM python:3.13-slim as base

# Common system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Python settings
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app
```

### Component Dockerfiles

Each component builds on the base:

```dockerfile
# Example: ai-db/Dockerfile
FROM ai-db-system:base

# Copy only this component
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY src/ ./src/

# Component-specific command
CMD ["python", "-m", "ai_db"]
```

### System Docker Compose

Single `docker-compose.yml` at root for running the complete system:

```yaml
version: '3.8'

services:
  # Build base image first
  base:
    image: ai-db-system:base
    build:
      context: .
      dockerfile: docker/base/Dockerfile
    command: echo "Base image built"

  ai-hub:
    build: ./ai-hub
    depends_on:
      - base
    ports:
      - "8000:8000"
    environment:
      - AI_DB_API_KEY=${AI_DB_API_KEY}
    volumes:
      - git-repos:/data/repos

  console:
    build: ./console
    depends_on:
      - base
    stdin_open: true
    tty: true
    volumes:
      - git-repos:/data/repos

  mcp-ai-db:
    build: ./mcp
    depends_on:
      - base
    command: ["ai-db-mcp"]
    volumes:
      - git-repos:/data/repos

  mcp-ai-frontend:
    build: ./mcp
    depends_on:
      - base
    command: ["ai-frontend-mcp"]
    volumes:
      - git-repos:/data/repos

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - git-repos:/data/repos:ro

volumes:
  git-repos:
```

## Part 5: CI/CD Standardization

### GitHub Actions Workflow

Simple, effective CI that tests each component:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [ai-shared, ai-db, ai-frontend, git-layer, console, mcp, ai-hub]
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Test Component
        working-directory: ./${{ matrix.component }}
        run: |
          poetry install
          poetry run pytest
          poetry run mypy .
          poetry run ruff check .
          poetry run black --check .
      
  integration:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Run Integration Tests
        run: |
          docker-compose build
          docker-compose run tests

  publish:
    if: startsWith(github.ref, 'refs/tags/')
    needs: [test, integration]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [ai-shared, ai-db, ai-frontend, git-layer]
    
    steps:
      - uses: actions/checkout@v4
      - name: Publish to PyPI
        working-directory: ./${{ matrix.component }}
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: |
          pip install poetry
          poetry publish --build
```

### Azure DevOps Pipeline

Equivalent pipeline for Azure DevOps:

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

jobs:
  - job: Test
    strategy:
      matrix:
        ai-shared:
          component: 'ai-shared'
        ai-db:
          component: 'ai-db'
        ai-frontend:
          component: 'ai-frontend'
        git-layer:
          component: 'git-layer'
        console:
          component: 'console'
        mcp:
          component: 'mcp'
        ai-hub:
          component: 'ai-hub'
    
    steps:
      - task: UsePythonVersion@0
        inputs:
          versionSpec: '3.13'
      
      - script: pip install poetry
        displayName: 'Install Poetry'
      
      - script: |
          cd $(component)
          poetry install
          poetry run pytest
          poetry run mypy .
          poetry run ruff check .
        displayName: 'Test $(component)'
  
  - job: Integration
    dependsOn: Test
    steps:
      - script: |
          docker-compose build
          docker-compose run tests
        displayName: 'Integration Tests'
```

## Part 6: Simplified Makefile

Essential commands only:

```makefile
# Root Makefile
.PHONY: help setup test lint format run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Set up development environment
	@echo "Setting up..."
	@for dir in ai-shared ai-db ai-frontend git-layer console mcp ai-hub; do \
		(cd $$dir && poetry install); \
	done

test: ## Run all tests
	@for dir in ai-shared ai-db ai-frontend git-layer console mcp ai-hub; do \
		echo "Testing $$dir..."; \
		(cd $$dir && poetry run pytest); \
	done
	@echo "Running integration tests..."
	@poetry run pytest tests/integration

lint: ## Run linters
	@for dir in ai-shared ai-db ai-frontend git-layer console mcp ai-hub; do \
		echo "Linting $$dir..."; \
		(cd $$dir && poetry run ruff check . && poetry run mypy .); \
	done

format: ## Format code
	@for dir in ai-shared ai-db ai-frontend git-layer console mcp ai-hub; do \
		(cd $$dir && poetry run black . && poetry run ruff check --fix .); \
	done

run: ## Run the system
	docker-compose up

clean: ## Clean up
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@docker-compose down -v
```

## Part 7: Quality Gates

### Code Quality Checklist
- [ ] All components follow standard structure
- [ ] No duplicate infrastructure code
- [ ] Consistent error handling patterns
- [ ] Shared code properly extracted
- [ ] All interfaces documented

### Testing Checklist
- [ ] 80% code coverage minimum
- [ ] All tests pass locally
- [ ] All tests pass in CI/CD

### Documentation Checklist
- [ ] All READMEs updated and consistent
- [ ] API documentation complete
- [ ] Contributing guide clear

### Developer Experience Checklist
- [ ] Setup takes < 5 minutes
- [ ] All make commands work
- [ ] Docker-compose brings up full system
- [ ] Clear error messages everywhere

## Part 8: Migration Guide

### For Each Component:

1. **Update Structure**
   ```bash
   # Move to new location
   mv ai-db components/libraries/ai-db
   
   # Restructure to standard layout
   mkdir -p components/libraries/ai-db/src/ai_db
   mv components/libraries/ai-db/*.py components/libraries/ai-db/src/ai_db/
   ```

2. **Update Imports**
   ```python
   # Old
   from transaction import Transaction
   
   # New
   from shared.protocols import TransactionProtocol
   ```

3. **Update Configuration**
   ```python
   # Old
   from typing import Optional
   import os
   
   class Config:
       api_key: Optional[str] = os.getenv("API_KEY")
   
   # New
   from pydantic_settings import BaseSettings
   
   class Config(BaseSettings):
       api_key: str
       
       class Config:
           env_prefix = "AI_DB_"
   ```

4. **Update Tests**
   ```python
   # Old
   from unittest.mock import Mock
   
   # New
   from shared.testing.fixtures import mock_ai_service
   ```

## Success Metrics

The standardization is complete when:

1. **Structural Consistency**
   - Single source of configuration
   - Uniform directory structure
   - Consistent file naming

2. **Code Consistency**
   - Same linting rules pass everywhere
   - Same test patterns used
   - Same error handling approach

3. **Operational Consistency**
   - Single command starts everything
   - All tests run the same way
   - Deployment is unified

4. **Documentation Consistency**
   - Same README structure
   - Same docstring format
   - Same example patterns

5. **Developer Satisfaction**
   - New developers productive in < 1 hour
   - No confusion about where things go
   - Clear patterns to follow

## Part 9: Developer Tools

### Health Check Script

Add a simple script to verify the development environment:

```bash
#!/bin/bash
# scripts/healthcheck.sh

echo "🔍 Checking AI-DB System environment..."
echo ""

# Check Python
if command -v python3.13 &> /dev/null; then
    echo "✅ Python 3.13 found"
else
    echo "❌ Python 3.13 not found (required)"
    exit 1
fi

# Check Poetry
if command -v poetry &> /dev/null; then
    echo "✅ Poetry found"
else
    echo "❌ Poetry not found - install with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
else
    echo "❌ Docker not found (required for running the system)"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✅ Git found"
else
    echo "❌ Git not found (required)"
    exit 1
fi

echo ""
echo "🎉 Environment ready for development!"
```

Make it executable: `chmod +x scripts/healthcheck.sh`

This plan transforms the fragmented codebase into a professional, maintainable system that appears to have been developed by a single, cohesive team.