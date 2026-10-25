export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

EXEC := docker compose exec pipeline
API := http://localhost:8000

.PHONY: help up down run inspect simulate schema-v2 api-logs shell reset

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Build and start the mock API + pipeline container
	docker compose up -d --build --wait

down: ## Stop everything
	docker compose down

run: ## Run the dlt pipeline (first run = full history, next runs = incremental)
	$(EXEC) python helpdesk_pipeline.py

inspect: ## Show tables, row counts, load history and the incremental cursor
	$(EXEC) python inspect_warehouse.py

simulate: ## Make the API change data: updates, inserts and soft deletes
	@curl -s -X POST "$(API)/admin/simulate" && echo

schema-v2: ## Make the API start sending a new nested field (schema evolution)
	@curl -s -X POST "$(API)/admin/schema-v2?enabled=true" && echo

api-logs: ## Tail the API logs
	docker compose logs -f api

shell: ## Shell inside the pipeline container
	docker compose exec -it pipeline bash

reset: ## Delete the DuckDB file and local dlt state (restart the API too: make down up)
	rm -rf warehouse/*.duckdb warehouse/*.wal .dlt/pipelines
