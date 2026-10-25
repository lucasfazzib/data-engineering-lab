PSQL := docker compose exec -T postgres psql -U lab -d lab -v ON_ERROR_STOP=1 -X

.PHONY: help up down clean run lesson exercise psql

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

up: ## Start Postgres (first start generates ~1M rows, takes ~20s)
	docker compose up -d --wait

down: ## Stop Postgres (data is kept in the volume)
	docker compose down

clean: ## Stop and delete the data volume (next `make up` re-seeds)
	docker compose down -v

run: ## Run every lesson in order
	@for f in lessons/*.sql; do echo; echo "################ $$f"; $(PSQL) -f /$$f || exit 1; done

lesson: ## Run one lesson: make lesson N=03
	$(PSQL) -f /$(firstword $(wildcard lessons/$(N)_*.sql))

exercise: ## Run your exercise file: make exercise N=01
	$(PSQL) -f /$(firstword $(wildcard exercises/ex$(N)_*.sql))

psql: ## Interactive psql
	docker compose exec postgres psql -U lab -d lab
