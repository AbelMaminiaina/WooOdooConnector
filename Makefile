.PHONY: help install run docker-up docker-down docker-logs test clean

help:
	@echo "WooCommerce <-> Odoo Connector - Available commands:"
	@echo ""
	@echo "  make install      - Install Python dependencies"
	@echo "  make run          - Run the API locally"
	@echo "  make docker-up    - Start with Docker Compose"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean temporary files"
	@echo ""

install:
	pip install -r requirements.txt

run:
	python run.py

docker-up:
	docker-compose up -d
	@echo ""
	@echo "API running at http://localhost:8000"
	@echo "Docs at http://localhost:8000/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f connector

docker-restart:
	docker-compose restart connector

docker-rebuild:
	docker-compose up -d --build

test:
	pytest

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=connector --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

format:
	black src/ tests/

lint:
	flake8 src/ tests/

env-example:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
		echo "Please edit .env with your credentials"; \
	else \
		echo ".env file already exists"; \
	fi
