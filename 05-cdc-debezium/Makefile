export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

APP := docker compose exec -T app python
PSQL := docker compose exec -T postgres psql -U postgres -d shop -X
KAFKA_BIN := docker compose exec -T kafka /opt/kafka/bin

.PHONY: help up down run register status topics watch workload slot replica verify-replica outbox psql logs

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

up: ## Start Postgres + Kafka + Kafka Connect (Debezium) + app (~2.3 GB RAM, ~60 s)
	docker compose up -d --build --wait

down: ## Stop everything (state is ephemeral: next up starts from scratch)
	docker compose down
	rm -f replica.duckdb replica.duckdb.wal

run: register ## Guided demo: snapshot -> live changes -> slot
	@echo "\n### 1. initial snapshot: every existing row arrives as op=r"; $(APP) watch.py --quiet-snapshot
	@echo "\n### 2. live changes: insert, updates, delete"; $(APP) workload.py
	@sleep 3
	@echo "\n### 3. the change events (note before/after on orders: REPLICA IDENTITY FULL)"; \
		$(APP) watch.py --quiet-snapshot --idle-seconds 4
	@echo "\n### 4. the replication slot Debezium is reading from"; $(MAKE) -s slot

register: ## Register (or update) the shop connector
	$(APP) connect.py register ../connectors/shop-connector.json

status: ## Connector status
	$(APP) connect.py status

topics: ## List topics
	$(KAFKA_BIN)/kafka-topics.sh --bootstrap-server localhost:9092 --list

watch: ## Pretty-print all change events from the beginning
	$(APP) watch.py

workload: ## Generate insert/update/delete in Postgres
	$(APP) workload.py

slot: ## Replication slots and the WAL they retain
	@$(PSQL) -c "select slot_name, plugin, active, confirmed_flush_lsn, \
		pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as retained_wal from pg_replication_slots"

replica: ## EXERCISE 2: apply the CDC stream to a DuckDB replica
	$(APP) replica.py

verify-replica: ## Compare source vs replica (ids and statuses)
	@$(PSQL) -t -A -c "select count(*), sum(id), string_agg(distinct status, ',' order by status) from orders"
	@docker compose exec -T app python -c "import duckdb; print(duckdb.connect('/lab/replica.duckdb', read_only=True).execute(\"select count(*), sum(id), string_agg(distinct status, ',' order by status) from orders\").fetchone())"

outbox: ## EXERCISE 3: register the outbox connector, write an order + event, watch the outbox topic
	$(APP) connect.py register ../connectors/outbox-connector.json
	$(APP) workload.py --outbox
	@sleep 3
	$(APP) watch.py --topics "^outbox\..*,^shopoutbox\..*" --raw --idle-seconds 4

psql: ## psql into the source database
	docker compose exec postgres psql -U postgres -d shop

logs: ## Kafka Connect logs
	docker compose logs -f connect
