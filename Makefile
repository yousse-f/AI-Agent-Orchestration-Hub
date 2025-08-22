# Makefile for AI Agent Orchestration Hub
# Professional development and deployment automation

.PHONY: help install test lint format security docker-build docker-run clean docs deploy

# Default target
help: ## Show this help message
	@echo "AI Agent Orchestration Hub - Development Commands"
	@echo "================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
install: ## Install all dependencies and setup development environment
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install pre-commit
	. venv/bin/activate && pre-commit install
	cp .env.example .env
	@echo "✅ Development environment setup complete!"
	@echo "📝 Remember to add your OPENAI_API_KEY to .env file"

# Code Quality
lint: ## Run all linting checks
	flake8 api/ tests/
	mypy api/
	@echo "✅ Linting complete!"

format: ## Format code using black and isort
	black api/ tests/
	isort api/ tests/
	@echo "✅ Code formatting complete!"

security: ## Run security checks
	bandit -r api/
	safety check
	@echo "✅ Security scan complete!"

# Testing
test: ## Run all tests with coverage
	pytest tests/ --cov=api --cov-report=html --cov-report=term
	@echo "✅ Tests complete! Coverage report in htmlcov/"

test-fast: ## Run tests without coverage (faster)
	pytest tests/ -x -v
	@echo "✅ Fast tests complete!"

test-integration: ## Run integration tests only
	pytest tests/test_integration.py -v
	@echo "✅ Integration tests complete!"

# Docker Operations
docker-build: ## Build production Docker image
	docker build -t ai-agents-hub:latest -f docker/Dockerfile .
	@echo "✅ Docker image built successfully!"

docker-run: ## Run the application in Docker
	docker-compose up -d
	@echo "✅ Application started! Available at http://localhost:8000"
	@echo "📖 API docs at http://localhost:8000/docs"

docker-stop: ## Stop Docker containers
	docker-compose down
	@echo "✅ Application stopped!"

docker-logs: ## Show application logs
	docker-compose logs -f ai-agents-api

# Production Operations
build-prod: ## Build optimized production image
	docker build -t ai-agents-hub:production --target production -f docker/Dockerfile .
	@echo "✅ Production image built!"

deploy-local: ## Deploy locally for testing
	docker-compose -f docker-compose.yml up -d
	@echo "✅ Local deployment complete!"
	@echo "🔍 Health check: curl http://localhost:8000/health"

# Development Utilities
dev-server: ## Start development server with auto-reload
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
	@echo "🚀 Development server starting..."

redis-start: ## Start Redis server locally
	redis-server --daemonize yes
	@echo "✅ Redis server started!"

redis-stop: ## Stop Redis server
	redis-cli shutdown
	@echo "✅ Redis server stopped!"

# Documentation
docs: ## Generate and serve documentation
	@echo "📚 API Documentation available at:"
	@echo "   - OpenAPI: http://localhost:8000/docs"
	@echo "   - ReDoc: http://localhost:8000/redoc"
	@echo "   - JSON Schema: http://localhost:8000/openapi.json"

# Cleanup
clean: ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Quality Assurance (CI/CD simulation)
ci-test: lint security test ## Run all CI checks locally
	@echo "✅ All CI checks passed!"

# Performance Testing
perf-test: ## Run performance tests
	locust --headless -u 10 -r 2 -t 30s --host http://localhost:8000
	@echo "✅ Performance tests complete!"

# Database Operations
db-reset: ## Reset Redis database
	redis-cli FLUSHDB
	@echo "✅ Redis database reset!"

# Environment Management
env-check: ## Check environment configuration
	@echo "🔍 Environment Configuration:"
	@echo "OPENAI_API_KEY: $$(if [ -n "$$OPENAI_API_KEY" ]; then echo "✅ Set"; else echo "❌ Missing"; fi)"
	@echo "REDIS_URL: $$(if [ -n "$$REDIS_URL" ]; then echo "✅ Set"; else echo "❌ Missing"; fi)"
	@python -c "import sys; print(f'Python: {sys.version}')"
	@docker --version 2>/dev/null || echo "❌ Docker not installed"
	@redis-cli --version 2>/dev/null || echo "❌ Redis CLI not available"

# Quick Start
quickstart: install docker-build docker-run ## Complete setup and start (one command)
	@echo ""
	@echo "🎉 AI Agent Orchestration Hub is ready!"
	@echo "==============================================="
	@echo "📖 API Documentation: http://localhost:8000/docs"
	@echo "🔍 Health Check: curl http://localhost:8000/health"
	@echo "🧪 Test Endpoint: curl -X POST http://localhost:8000/analyze -H 'Content-Type: application/json' -d '{\"query\":\"test\"}'"
	@echo ""
	@echo "📝 Next steps:"
	@echo "  1. Add your OPENAI_API_KEY to .env file"
	@echo "  2. Run 'make test' to verify everything works"
	@echo "  3. Check 'make help' for more commands"
