# Study guide

How to use this repo to get — and stay — interview-ready for **Data Engineer / Senior Data Engineer** roles:
what the market asks for, where each skill is practiced here, a 12-week plan, and interview preparation.

Written for someone who already knows Spark/Databricks well and wants to cover the rest of the modern stack.

---

## 1. What the market asks for

Job descriptions vary, but they cluster around the same blocks. Senior roles add **design, trade-offs and ownership**
on top of the tooling.

| Block | Typical asks | In this repo |
|---|---|---|
| **SQL & data modeling** | window functions, CTEs, query tuning, Kimball (facts/dims, SCD), sometimes Data Vault | 01, 02, **13** |
| **Python for data** | clean, typed, tested code; APIs; packaging; CLIs | 03, 04, 05, 13 |
| **Cloud warehouse / lakehouse** | Snowflake, Databricks, BigQuery, Redshift; Delta / **Iceberg** | 06, 12, 14 |
| **Transformation** | **dbt** (models, tests, incremental, snapshots, docs, CI) | 01, **13** |
| **Ingestion** | ELT tools (Fivetran/Airbyte), custom API connectors, file ingestion | 03, 13 |
| **CDC** | Debezium, log-based replication, outbox | 02, **05** |
| **Streaming** | **Kafka** (+ Kinesis/Event Hubs), Spark Structured Streaming, Flink | 04, 06, 09 |
| **Orchestration** | **Airflow** (most common), Dagster, Prefect; idempotency and backfills | 07 |
| **Data quality & governance** | tests, contracts, lineage, catalogs, observability, PII | 01, 08, 10, **13** |
| **DevEx / DataOps** | Git, CI/CD, Docker, code review, environments | every folder, `.github/` |
| **Cloud & IaC** | AWS/Azure/GCP services, Terraform | *not covered — see §7* |
| **Cost & performance** | partitioning, clustering, warehouse sizing, FinOps | 02, 06, 12, 14 |
| **AI-adjacent data work** | pipelines for unstructured data, embeddings / vector stores, feeding RAG/ML | *not covered — see §7* |

What separates **senior** candidates in interviews:
- explaining **why** (trade-offs, alternatives rejected) — the ADRs in `13/docs/adr` are the format to practice;
- designing for **failure**: retries, idempotency, backfills, late data, schema changes, bad records;
- **operating** systems: monitoring, SLAs, incidents, cost;
- influence: code review, standards, mentoring, talking to stakeholders.

---

## 2. Skill matrix — self-assessment

Score yourself 0–3 (0 = never used · 1 = followed a tutorial · 2 = can build it alone · 3 = can design it and
explain the trade-offs under pressure). Re-score every 4 weeks.

| Skill | Practice in | Score |
|---|---|---|
| dbt: layers, ref/source, materializations | 01, 13 | |
| dbt: incremental + late data, snapshots | 01 (ex. 4, 5) | |
| dbt: tests, contracts, unit tests, docs | 01, 13 | |
| Dimensional modeling (grain, SCD, conformed dims) | 13 + ADR 0002 | |
| Postgres plans and indexes | 02 (lesson 01, ex. 1–2) | |
| MVCC, WAL, replication slots | 02 (lessons 02–03) | |
| Idempotent loading (upsert, MERGE, delete+insert) | 02 (lesson 05, ex. 5) | |
| API ingestion: pagination, state, incremental | 03 | |
| Kafka: partitions, keys, groups, offsets | 04 | |
| Delivery semantics, idempotent consumers, DLQ | 04 (ex. 3–5) | |
| CDC with Debezium, outbox | 05 | |
| Structured Streaming: watermarks, MERGE, checkpoints | 06 | |
| Airflow: idempotent DAGs, backfill | 07 | |
| Data contracts in CI | 08 | |
| Flink SQL: windows, state, temporal joins | 09 | |
| Lineage (OpenLineage) | 10 | |
| Iceberg internals, Trino | 12 | |
| Snowflake features and cost model | 14 | |
| System design for data platforms | §5 of this guide | |

---

## 3. How to study one example

1. **Read** the README sections 1–3 (what, concepts, architecture) before running anything.
2. **Run** `make up && make run` and read the output top to bottom. Predict each step before it prints.
3. **Break it** on purpose: kill a container, change a key, remove a column. Note what happened in `NOTES.md`.
4. **Exercises**: implement the TODOs without looking at docs first; then read the docs and improve.
5. **Interview questions**: answer each one **out loud** in under 2 minutes. If you can't, go back to step 1.
6. **Write** the "what broke and how I fixed it" table in `NOTES.md` — those are your interview stories.
7. `make down`.

---

## 4. A 12-week plan (~6–8 h/week)

| Week | Focus | Deliverable |
|---|---|---|
| 1 | 01 dbt + DuckDB: exercises 1–3 | staging + fact + tests green |
| 2 | 01: incremental, snapshots, docs (ex. 4–8) | notes on late data and SCD2 strategies |
| 3 | 13 Olist: read ADRs, run, trace lineage, break things (study path §) | one extension merged (e.g. incremental `fct_order_items`) |
| 4 | 02 Postgres: lessons + exercises 1, 2, 5 | tuned query with before/after plans |
| 5 | 02: WAL/slots/partitioning (ex. 3–4) + 03 dlt | slot monitoring query; incremental pipeline with hard deletes |
| 6 | 04 Kafka: all exercises | idempotent consumer + DLQ |
| 7 | 05 Debezium: replica + outbox | CDC sink that survives replays |
| 8 | 06 Spark Streaming → Delta | streaming MERGE with watermark |
| 9 | 07 Airflow + 08 data contracts | idempotent DAG with backfill; contract check in CI |
| 10 | 09 Flink + 12 Iceberg/Trino | windowed aggregation; time travel + partition evolution |
| 11 | 14 Snowflake + 10 lineage | Snowflake version of a 13 mart; lineage graph |
| 12 | 11 capstone + interview mock week | end-to-end demo + 3 system design write-ups |

Every week: 3 SQL problems (§5.1) and 1 system-design prompt (§5.2), answered out loud.

---

## 5. Interview preparation

### 5.1 SQL patterns to master

All of these appear in the repo — practice writing them from memory:

| Pattern | Example in the repo |
|---|---|
| Dedup / latest row per key (`row_number` / `qualify`) | `01 stg_bookstore__orders`, `13 int_order_reviews__latest` |
| Top-N per group | `13 analyses/top_categories_by_region.sql` |
| Running totals, MoM growth (`sum() over`, `lag`) | `13 mart_monthly_sales` |
| Pareto / cumulative share | `13 mart_seller_scorecard` |
| Cohorts and retention | `13 mart_customer_cohorts` |
| Avoiding fan-out (aggregate before join) | `13 fct_orders` |
| SCD2 point-in-time join | `01` exercise 6 |
| Upsert / MERGE / idempotent window reload | `02 lesson 05` |
| Gaps and islands, sessionization | *practice*: sessionize `04` events by 30-min inactivity |

### 5.2 System design for data — a framework

Use the same skeleton for every prompt and **say the trade-offs out loud**:

1. **Requirements**: consumers, freshness (batch / micro-batch / real-time), volume and growth, SLAs, retention, compliance (PII).
2. **Sources and ingestion**: CDC vs API vs files vs events; full vs incremental; backfill strategy.
3. **Storage**: warehouse vs lakehouse; table format; partitioning/clustering; layers (raw → staging → marts).
4. **Processing**: batch (dbt/Spark) vs streaming (Kafka + Flink/Spark); idempotency; late and out-of-order data.
5. **Serving**: BI, reverse ETL, APIs, ML features; semantic layer.
6. **Quality and observability**: tests, contracts, freshness, volume anomalies, lineage, alerting, on-call.
7. **Failure modes**: what if a source is down 2 days, a schema changes, a job runs twice, a bad deploy ships?
8. **Cost**: compute sizing, storage tiers, query patterns, who pays.

Practice prompts:
- Design the analytics platform for an e-commerce like Olist (start from example 13, then make it real-time).
- Replicate 200 Postgres tables into the lakehouse with < 5 min latency (examples 02, 05, 06).
- A daily revenue dashboard is wrong 1 day per month — design the fix and the prevention.
- Ingest 50 SaaS APIs with different rate limits and schemas (example 03).
- Real-time fraud features from card transactions with a 1-second SLA (examples 04, 09).
- Migrate a Hive/Parquet data lake to Iceberg or Delta with zero downtime (examples 06, 12).

### 5.3 Behavioral (senior)

Prepare 6–8 stories in **STAR** format (Situation, Task, Action, Result — with numbers):
- an incident you led and the postmortem changes that followed;
- a design decision you defended — and one where you changed your mind;
- a pipeline you made faster or cheaper (how much?);
- a data-quality problem that reached a stakeholder, and how you rebuilt trust;
- mentoring / raising the bar of a team (code review, standards);
- pushing back on a requirement, or negotiating scope with a stakeholder.

The "what broke and how I fixed it" tables in each `NOTES.md` are raw material for these stories.

---

## 6. Using this repo as a portfolio

- **Pin** the repository on your GitHub profile; the root README and example 13 are the shop window.
- In interviews, walk through **13**: problem → ADRs → data-quality findings → model → insights → what you'd change in production. Practice it in 5 minutes.
- Add **your own extension** to 13 (incremental facts, SCD2 customers, a Snowflake target, an orchestrator) — "I extended it with X because Y" is stronger than any tutorial.
- Write a short post about one finding (e.g. "late deliveries cut review scores in half") with the SQL behind it.
- Keep CI green: a red badge on a portfolio repo is worse than no badge.

---

## 7. Gaps this repo does not cover (yet) — and free ways to fill them

| Gap | Free option |
|---|---|
| Real Snowflake | 30-day trial account (credits included); example 14 covers the local part |
| Databricks | Databricks Free Edition |
| Cloud services (S3, Glue, Lambda, ADLS, Event Hubs) | AWS / Azure free tiers; LocalStack for local AWS emulation |
| Terraform | provision the 13 project's storage + warehouse on a free tier |
| Data observability | Elementary (dbt package) on top of example 13 |
| AI-adjacent pipelines | pgvector on Postgres: embed Olist review comments and build a semantic search |

---

## 8. References

**Books**
- *Designing Data-Intensive Applications* — Martin Kleppmann (storage, replication, streams: the theory under 02, 04, 05)
- *Fundamentals of Data Engineering* — Joe Reis & Matt Housley (the lifecycle and the vocabulary interviewers use)
- *The Data Warehouse Toolkit* — Ralph Kimball & Margy Ross (dimensional modeling: example 13)
- *Streaming Systems* — Tyler Akidau, Slava Chernyak & Reuven Lax (watermarks and windows: 06, 09)

**Official docs** (the best source for every tool here): [dbt](https://docs.getdbt.com/) ·
[DuckDB](https://duckdb.org/docs/) · [PostgreSQL](https://www.postgresql.org/docs/current/) ·
[dlt](https://dlthub.com/docs) · [Kafka](https://kafka.apache.org/documentation/) ·
[Debezium](https://debezium.io/documentation/) · [Spark Structured Streaming](https://spark.apache.org/docs/latest/streaming/) ·
[Delta Lake](https://docs.delta.io/) · [Airflow](https://airflow.apache.org/docs/) · [Flink](https://nightlies.apache.org/flink/flink-docs-stable/) ·
[Iceberg](https://iceberg.apache.org/docs/latest/) · [Trino](https://trino.io/docs/current/) · [OpenLineage](https://openlineage.io/docs/)
