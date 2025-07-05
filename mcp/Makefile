.PHONY: help install install-dev test test-unit test-integration lint type-check format clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install        Install the package"
	@echo "  make install-dev    Install with development dependencies"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make lint           Run linting checks"
	@echo "  make type-check     Run type checking"
	@echo "  make format         Format code with black"
	@echo "  make clean          Clean build artifacts"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-run     Run with Docker Compose"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-unit:
	pytest -v tests/unit

test-integration:
	pytest -v tests/integration

lint:
	ruff check src tests

type-check:
	mypy src tests

format:
	black src tests
	ruff check --fix src tests

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-run:
	docker-compose up

# Development shortcuts
dev-ai-db:
	AI_DB_USE_MOCKS=true AI_DB_LOG_FORMAT=console python -m src.ai_db_server

dev-ai-frontend:
	AI_FRONTEND_USE_MOCKS=true AI_FRONTEND_LOG_FORMAT=console python -m src.ai_frontend_server