export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

EXEC := docker compose exec dbt

.PHONY: help up down run load-batch1 load-batch2 seed build test snapshot freshness docs show dbt shell reset

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

up: ## Build the image and start the container
	docker compose up -d --build

down: ## Stop and remove the container
	docker compose down

run: load-batch1 seed build ## Full first run: load batch_1 -> seed -> build

load-batch1: ## Reset raw schema and load landing/batch_1
	$(EXEC) python /lab/scripts/load_landing.py batch_1 --reset

load-batch2: ## Load landing/batch_2 (customers/books replaced, orders/items appended)
	$(EXEC) python /lab/scripts/load_landing.py batch_2

seed: ## dbt seed
	$(EXEC) dbt seed

build: ## dbt build (run + test + seed + snapshot, in DAG order)
	$(EXEC) dbt build

test: ## dbt test
	$(EXEC) dbt test

snapshot: ## dbt snapshot
	$(EXEC) dbt snapshot

freshness: ## dbt source freshness
	$(EXEC) dbt source freshness

docs: ## Generate docs and serve them on http://localhost:8080 (Ctrl+C to stop)
	$(EXEC) dbt docs generate
	$(EXEC) dbt docs serve --host 0.0.0.0 --port 8080 --no-browser

show: ## Run ad-hoc SQL: make show Q="select * from {{ ref('dim_customers') }}"
	$(EXEC) dbt show --inline "$(Q)" --limit 50

dbt: ## Any dbt command: make dbt ARGS="ls --resource-type model"
	$(EXEC) dbt $(ARGS)

shell: ## Shell inside the container
	docker compose exec -it dbt bash

reset: ## Delete the DuckDB file and dbt artifacts (start from scratch)
	rm -f warehouse/*.duckdb warehouse/*.duckdb.wal
	rm -rf bookstore/target bookstore/logs
