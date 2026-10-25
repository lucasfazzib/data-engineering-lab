export LAB_UID := $(shell id -u)
export LAB_GID := $(shell id -g)

APP := docker compose exec -T app python
KAFKA_BIN := docker compose exec -T kafka /opt/kafka/bin

.PHONY: help up up-ui down run topics describe produce consume lag groups reset-offsets rebalance-demo shell

help: ## List targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

up: ## Start Kafka (KRaft) + app container
	docker compose up -d --build --wait

up-ui: ## Same + Kafka UI on http://localhost:8080 (~400 MB more)
	docker compose --profile ui up -d --build --wait

down: ## Stop everything and delete topics (no volume: Kafka data is ephemeral here)
	docker compose --profile ui down

run: topics ## Guided demo: produce, consume, lag, second group, crash + redelivery
	@echo "\n### 1. produce 1000 keyed events"; $(APP) producer.py --count 1000
	@echo "\n### 2. group g1 consumes everything (manual commits)"; $(APP) consumer.py --group g1 --name c1
	@echo "\n### 3. lag of g1 is now 0"; $(APP) admin.py lag g1
	@echo "\n### 4. produce 300 more -> g1 lags by 300"; $(APP) producer.py --count 300; $(APP) admin.py lag g1
	@echo "\n### 5. a NEW group g2 reads the whole topic independently"; $(APP) consumer.py --group g2 --name x1
	@echo "\n### 6. g1 crashes after 150 msgs with commit-every=100 -> 50 msgs will be processed twice"
	-@$(APP) consumer.py --group g1 --name c1 --crash-after 150 --commit-every 100
	@$(APP) admin.py lag g1
	@echo "\n### 7. restart: waits for the dead member's session.timeout (10s), then reprocesses from the last commit"
	@$(APP) consumer.py --group g1 --name c1 --idle-seconds 20

topics: ## Create the lab topics
	$(APP) admin.py create

describe: ## Describe topics
	$(APP) admin.py describe

produce: ## Produce N events: make produce N=500 [ARGS="--no-key"]
	$(APP) producer.py --count $(or $(N),1000) $(ARGS)

consume: ## Consume with a group: make consume GROUP=g1 NAME=c1 [ARGS="--forever"]
	docker compose exec app python consumer.py --group $(or $(GROUP),g1) --name $(or $(NAME),c1) $(ARGS)

lag: ## Show lag: make lag GROUP=g1
	$(APP) admin.py lag $(or $(GROUP),g1)

groups: ## Describe all consumer groups with the Kafka CLI
	$(KAFKA_BIN)/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups

reset-offsets: ## Rewind a group: make reset-offsets GROUP=g1 TO="--to-earliest" (group must be inactive)
	$(KAFKA_BIN)/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group $(or $(GROUP),g1) \
		--topic orders --reset-offsets $(or $(TO),--to-earliest) --execute

rebalance-demo: ## 3 consumers in one group share 6 partitions
	@$(APP) producer.py --count 600 > /dev/null
	@docker compose exec -T app sh -c 'for n in a b c; do python consumer.py --group rb --name $$n --idle-seconds 8 & done; wait'

shell: ## Shell in the app container
	docker compose exec -it app bash
