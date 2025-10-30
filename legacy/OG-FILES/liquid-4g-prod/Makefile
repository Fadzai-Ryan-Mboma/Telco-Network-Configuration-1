# Makefile for Liquid4G

.PHONY: help install dev-install test test-cov lint format clean run-api run-ui migrate docker-build docker-up docker-down

help:  ## Show this help message
	@echo "Liquid4G - Make Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

dev-install:  ## Install development dependencies
	pip install -e ".[dev]"

test:  ## Run tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	pytest tests/ -v --cov=liquid4g --cov-report=html --cov-report=term

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v -m unit

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v -m integration

lint:  ## Run linters
	ruff check src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/
	isort src/ tests/

format-check:  ## Check code formatting
	black --check src/ tests/
	isort --check src/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -f .coverage

run-api:  ## Run REST API server
	python -m liquid4g api

run-ui:  ## Run Streamlit UI
	python -m liquid4g ui

migrate:  ## Run database migrations
	python -m liquid4g migrate

optimize:  ## Run optimization (example: make optimize SITE=HARARE_001)
	python -m liquid4g optimize --site-id=$(SITE)

docker-build:  ## Build Docker image
	docker-compose -f docker/docker-compose.yml build

docker-up:  ## Start Docker services
	docker-compose -f docker/docker-compose.yml up -d

docker-down:  ## Stop Docker services
	docker-compose -f docker/docker-compose.yml down

docker-logs:  ## View Docker logs
	docker-compose -f docker/docker-compose.yml logs -f

docker-shell:  ## Shell into Docker container
	docker-compose -f docker/docker-compose.yml exec app bash

setup-dev:  ## Setup development environment
	@echo "Setting up development environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"
	@echo "Then run: make dev-install"

check:  ## Run all checks (lint + test)
	make lint
	make test

all:  ## Install, lint, test, and build
	make dev-install
	make format
	make lint
	make test
