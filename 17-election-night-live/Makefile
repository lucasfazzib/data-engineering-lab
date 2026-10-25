export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

EXEC := docker compose run --rm --no-deps poller

.PHONY: help up down run poll once backfill test lint fmt logs clean

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Build and start the poller (every 60 s) and the dashboard on http://localhost:8501
	docker compose up -d --build
	@echo "Dashboard: http://localhost:8501"

down: ## Stop everything (data stays in ./data)
	docker compose down

run: up ## Alias of up: the pipeline is continuous

once: ## One polling pass (Brazil + 27 states), then exit
	$(EXEC) python -m election.poller --once

backfill: ## Load raw captures: make backfill DIR=path/with/json.gz
	$(EXEC) python -m election.poller --backfill $(DIR)

test: ## Unit tests + dashboard smoke test (no network)
	$(EXEC) pytest -q

lint: ## ruff
	$(EXEC) ruff check src dashboard tests
	$(EXEC) ruff format --check src dashboard tests

fmt: ## Auto-format
	$(EXEC) ruff format src dashboard tests
	$(EXEC) ruff check --fix src dashboard tests

logs: ## Follow the poller
	docker compose logs -f poller

clean: ## Delete collected data (bronze + silver)
	rm -rf data
