PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
COMPOSE ?= docker compose -f infra/docker/compose.yml

.PHONY: setup test lint format format-check typecheck no-ai check docker-up docker-down health clean

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "apps/api[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy

no-ai:
	bash tools/dev/check-no-ai.sh

check: lint format-check typecheck no-ai test

docker-up:
	$(COMPOSE) up -d --build

docker-down:
	$(COMPOSE) down

health:
	curl -fsS http://localhost:8000/health

clean:
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
