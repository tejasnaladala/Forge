.PHONY: install dev test lint format cli clean docker-up docker-down

# Install all dependencies including development tools.
install:
	pip install -e ".[all,dev]"

# Start the API server in development mode with hot reload.
dev:
	uvicorn forge.api.app:create_app --factory --reload --port 8626

# Run the test suite with coverage reporting.
test:
	pytest tests/ -v --cov=forge

# Run the linter.
lint:
	ruff check forge/

# Format all source files.
format:
	ruff format forge/ tests/

# Install the package and display CLI help.
cli:
	pip install -e . && forge --help

# Remove build artifacts and caches.
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	rm -rf .pytest_cache *.egg-info dist build

# Start all services using Docker Compose.
docker-up:
	docker compose up -d

# Stop all services.
docker-down:
	docker compose down
