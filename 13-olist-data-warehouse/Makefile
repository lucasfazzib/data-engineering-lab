export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

EXEC := docker compose exec -T dwh
DBT := docker compose exec -T -w /lab/olist_dbt dwh dbt

.PHONY: help up down run ingest deps build test docs dashboard test-dashboard lint fmt ci show shell clean

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Build the image and start the container
	docker compose up -d --build --wait

down: ## Stop the container
	docker compose down

run: ingest deps build ## Full pipeline: extract+load -> dbt deps -> dbt build

ingest: ## Download the Kaggle dataset (cached) and load it into raw.*
	$(EXEC) python ingestion/extract_load.py

deps: ## Install dbt packages (dbt_utils)
	$(DBT) deps

build: ## dbt build: seeds, models, unit tests and data tests in DAG order
	$(DBT) build

test: ## dbt test only
	$(DBT) test

docs: ## Generate and serve dbt docs on http://localhost:8080 (Ctrl+C to stop)
	$(DBT) docs generate
	$(DBT) docs serve --host 0.0.0.0 --port 8080 --no-browser

dashboard: ## Streamlit dashboard on http://localhost:8501 (Ctrl+C to stop)
	$(EXEC) streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

test-dashboard: ## Smoke-test the dashboard (renders without exceptions, needs a built warehouse)
	docker compose exec -T -w /lab/dashboard dwh python test_app.py

lint: ## sqlfluff (dbt templater) + ruff
	$(EXEC) ruff check ingestion dashboard
	$(EXEC) ruff format --check ingestion dashboard
	docker compose exec -T -w /lab/olist_dbt dwh sqlfluff lint models tests analyses

fmt: ## Auto-fix SQL and Python style
	$(EXEC) ruff format ingestion dashboard
	docker compose exec -T -w /lab/olist_dbt dwh sqlfluff fix models tests analyses

ci: ## What CI runs: empty raw tables -> dbt build --empty (schema + unit tests) -> lint
	$(EXEC) env DUCKDB_PATH=/tmp/ci.duckdb python ingestion/extract_load.py --empty
	docker compose exec -T -w /lab/olist_dbt -e DUCKDB_PATH=/tmp/ci.duckdb dwh sh -c 'dbt deps && dbt build --empty'

show: ## Ad-hoc query: make show Q="select * from {{ ref('mart_monthly_sales') }}"
	$(DBT) show --inline "$(Q)" --limit 50

shell: ## Shell inside the container
	docker compose exec -it dwh bash

clean: ## Remove the warehouse file and dbt artifacts (keeps the downloaded dataset)
	rm -f warehouse/*.duckdb warehouse/*.wal warehouse/ingestion_manifest.json
	rm -rf olist_dbt/target olist_dbt/logs olist_dbt/dbt_packages
