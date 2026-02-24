.PHONY: install dev test lint format cli clean docker-up docker-down

install:
	pip install -e ".[all,dev]"

dev:
	uvicorn forge.api.app:create_app --factory --reload --port 8626

test:
	pytest tests/ -v --cov=forge

lint:
	ruff check forge/

format:
	ruff format forge/ tests/

cli:
	pip install -e . && forge --help

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	rm -rf .pytest_cache *.egg-info dist build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
