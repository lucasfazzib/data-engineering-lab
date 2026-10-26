export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

TOOLS := docker compose run --rm tools
KAFKA := docker compose exec -T kafka /opt/kafka/bin
N ?= 300
RATE ?= 0

.PHONY: help up up-ui notebook down run prepare send send-live topics consume-in consume-out mongo-count logs test lint fmt clean

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

up: ## Build and start Kafka, MongoDB, api-ingest, the Spark stream and the dashboard
	mkdir -p data
	docker compose up -d --build --wait kafka mongo api-ingest dashboard
	docker compose up -d spark-stream
	@echo ""
	@echo "  API (Swagger)  http://localhost:8000/docs"
	@echo "  Dashboard      http://localhost:8501"

up-ui: ## Also start Mongo Express on http://localhost:8081
	docker compose --profile ui up -d mongo-express

notebook: ## JupyterLab with the streaming notebook on http://localhost:8888
	docker compose --profile notebook up -d --build notebook

down: ## Stop everything (MongoDB data and checkpoints stay in volumes)
	docker compose --profile ui --profile notebook --profile tools down

run: up prepare send ## Everything: start, prepare N invoices (default 300), stream them

prepare: ## Kaggle CSV -> data/invoice_items.jsonl (N invoices; N=0 = all)
	$(TOOLS) python data_prep/csv_to_json.py --invoices $(N)

send: ## Input client: POST every item to the API (RATE=20 to watch it live)
	$(TOOLS) sh -c 'python client/api_client.py --url $$API_URL --rate $(RATE)'

send-live: ## Slow stream (20 items/s) to watch the dashboard update
	$(MAKE) --no-print-directory send RATE=20

topics: ## List topics with partitions and offsets
	$(KAFKA)/kafka-topics.sh --bootstrap-server localhost:9092 --describe
	$(KAFKA)/kafka-get-offsets.sh --bootstrap-server localhost:9092

consume-in: ## Peek at the first 5 messages of ingestion-topic
	$(KAFKA)/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic ingestion-topic --from-beginning --max-messages 5 --formatter-property print.key=true

consume-out: ## Peek at the first 5 messages Spark wrote to spark-output
	$(KAFKA)/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic spark-output --from-beginning --max-messages 5 --formatter-property print.key=true

mongo-count: ## Invoices and items stored in MongoDB
	docker compose exec -T mongo mongosh --quiet -u dashboard -p dashboard --authenticationDatabase invoices invoices \
		--eval 'const r = db.invoices.aggregate([{$$group: {_id: null, invoices: {$$sum: 1}, items: {$$sum: {$$size: "$$items"}}}}]).toArray()[0]; printjson(r)'

logs: ## Follow the Spark stream
	docker compose logs -f spark-stream

test: ## Unit tests (no services needed)
	$(TOOLS) pytest -q

lint: ## ruff
	$(TOOLS) ruff check .
	$(TOOLS) ruff format --check .

fmt: ## Auto-format
	$(TOOLS) ruff format .
	$(TOOLS) ruff check --fix .

clean: ## down + delete MongoDB data, checkpoints and the prepared JSON (keeps the Kaggle download)
	docker compose --profile ui --profile notebook --profile tools down -v
	rm -f data/invoice_items.jsonl
