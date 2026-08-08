PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
COMPOSE ?= docker compose -f infra/docker/compose.yml
SERVICES ?= services/*/

.PHONY: setup test lint format format-check typecheck no-ai check docker-up docker-down health clean services-install

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "libs/backend-core[dev]"
	$(PIP) install -e "apps/api[dev]"
	$(MAKE) services-install

services-install:
	for s in $(SERVICES); do \
		$(PIP) install -e "$$s[dev]"; \
	done

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

contracts:
	bash tools/dev/check-contracts.sh

check: lint format-check typecheck no-ai contracts test

docker-up:
	$(COMPOSE) up -d --build

docker-down:
	$(COMPOSE) down

health:
	curl -fsS http://localhost:8000/health

clean:
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: fe-install fe-lint fe-typecheck fe-build fe-test fe-check

fe-install:
	npm install

fe-lint:
	npm run lint

fe-typecheck:
	npm run typecheck

fe-build:
	npm run build

fe-test:
	npm test

fe-check: fe-lint fe-typecheck fe-test
