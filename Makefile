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

test-docker: ## Run tests in Docker with all dependencies
	docker-compose build base
	docker-compose run test-runner

clean: ## Clean up
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@docker-compose down -v