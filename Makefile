.PHONY: help install dev build clean test lint format docker-up docker-down docker-logs

help:
	@echo "Chimera Analytics - Available Commands"
	@echo ""
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start development environment"
	@echo "  make build        - Build all packages"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Lint all code"
	@echo "  make format       - Format all code"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make docker-logs  - View Docker logs"
	@echo "  make clean        - Clean build artifacts"

install:
	npm install
	cd packages/agents && pip install -r requirements.txt

dev:
	docker-compose up -d
	npm run dev:api

build:
	npm run build

test:
	npm run test

lint:
	npm run lint
	cd packages/agents && pylint src/

format:
	npm run format
	cd packages/agents && black src/ && isort src/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	rm -rf node_modules
	rm -rf packages/*/node_modules
	rm -rf packages/*/dist
	rm -rf packages/agents/__pycache__
	rm -rf packages/agents/.pytest_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +
