export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

RUN := docker compose run --rm app
DBT := docker compose run --rm -w /lab/transform app dbt

.PHONY: help build collect enrich transform snapshot run app test lint fmt ci show clean

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

build: ## Build the image
	docker compose build

collect: ## Collect all sources (polite: cache ~1 day, 1 request / 2 s per host)
	$(RUN) python -m corridas.ingest

enrich: ## IBGE municipalities + centroids (once; cached for a year)
	$(RUN) python -m corridas.enrich

transform: ## dbt: seeds, snapshot (SCD2), models and tests
	$(DBT) build

snapshot: ## Only the SCD2 snapshot of prices/status
	$(DBT) snapshot

run: enrich collect transform ## Everything, in order (daily job)

app: ## Streamlit on http://localhost:8501
	docker compose up app-ui

test: ## Unit tests (parsers with saved HTML fixtures, HTTP client, enrichment)
	$(RUN) pytest -q

lint: ## ruff + sqlfluff
	$(RUN) ruff check src app tests scripts
	$(RUN) ruff format --check src app tests scripts
	docker compose run --rm -w /lab/transform app sqlfluff lint models

fmt: ## Auto-format
	$(RUN) ruff format src app tests scripts
	$(RUN) ruff check --fix src app tests scripts

ci: ## What CI runs: synthetic data -> dbt build (twice, to exercise the snapshot) in a temp folder
	$(RUN) sh -c 'export CORRIDAS_DATA=/tmp/ci && python scripts/fixture_data.py && cd transform && dbt build && dbt build'

show: ## Ad-hoc query: make show Q="select * from {{ ref('mart_upcoming_races') }}"
	$(DBT) show --inline "$(Q)" --limit 30

clean: ## Delete collected data, cache and the warehouse
	rm -rf data transform/target transform/logs
