# CLAUDE.md

Context for resuming work on this repo in a new session.

## Purpose
- A public study lab for the modern data stack, also used as a portfolio and as material for others to clone.
- The learner already knows Spark/Databricks/Delta, Python, SQL and cloud; the repo covers dbt, DuckDB,
  Postgres internals, dlt, Kafka, Debezium, Spark Streaming, Airflow, Flink, contracts, lineage, Iceberg/Trino, Snowflake.
- Talk to the user in **PT-BR**. Repo docs (README, STUDY_GUIDE, ADRs) are in **English**; NOTES.md may be in PT-BR.

## Privacy rules (non-negotiable)
- Never commit personal information: names, personal emails, tokens, API keys, account ids, machine details.
- Git identity for this repo is the GitHub handle + noreply address (repo-local `git config`). Keep it that way.
- Credentials in compose files are local-only dummies. Real secrets only in git-ignored files.
- Published ports bind to loopback only (`"127.0.0.1:5432:5432"`), so dummy credentials are never reachable from the network.
- Datasets are downloaded at run time, never committed (`data/`, `*.duckdb`, manifests are git-ignored).
- `secret-scan` workflow (gitleaks) runs on every push.

## Role: senior mentor in LEARNING MODE
- Examples 01–12, 14: build infra + a working skeleton, explain concepts, leave exercises as `TODO`s.
  Validate that every exercise is solvable (throwaway copy, never committed). Then review the learner's code
  like a demanding reviewer (correctness, idempotency, performance, naming, tests).
- Example 13 is the exception: a complete reference implementation (portfolio).
- One example at a time, only when asked.

## Conventions
- Folder per example: `NN-kebab-name/` with `docker-compose.yml`, `Makefile` (`help`/`up`/`run`/`down`), `README.md`, `NOTES.md`.
- Examples never depend on another folder to run.
- README sections, in order: 1. What this example teaches · 2. Key concepts (with Spark/Databricks analogies) ·
  3. Architecture (Mermaid) · 4. How to run · 5. Exercises · 6. Interview questions.
- Lean compose: pinned versions (prefer releases > 2 weeks old), `mem_limit` on every service, weight flagged.
- Containers that write to bind mounts run as the host user (`LAB_UID`/`LAB_GID` exported by the Makefile).
- Postgres healthchecks use `-h 127.0.0.1` (the init-time server only listens on the unix socket).
- Postgres 18 images mount data at `/var/lib/postgresql` (not `.../data`).
- Kafka: `apache/kafka` in KRaft mode. MinIO: upstream stopped publishing images; use a maintained community build.
- Commits: Conventional Commits (`feat(NN-name): ...`, `docs: ...`, `ci: ...`).

## Definition of done for an example
1. `make up && make run && make down` works from scratch; exercises validated as solvable.
2. Status updated in the root README table and below.
3. Conventional commit (push when the user asks or has already approved pushing).

## Status
| # | Example | Status |
|---|---------|--------|
| 01 | dbt + DuckDB | in progress — skeleton verified; learner doing exercises |
| 02 | Postgres for data engineers | in progress — 5 lessons + 5 exercises verified |
| 03 | dlt incremental ingestion | in progress — mock API + pipeline verified |
| 04 | Kafka basics | in progress — guided demo verified |
| 05 | CDC with Debezium | in progress — snapshot/stream demo verified; replica + outbox solvable |
| 06 | Spark Structured Streaming → Delta on S3 | todo |
| 07 | Airflow | todo |
| 08 | Data contracts + CI | todo |
| 09 | Flink basics | todo |
| 10 | Lineage with OpenLineage/Marquez | todo |
| 11 | Capstone end-to-end | todo |
| 12 | Iceberg + Trino | todo |
| 13 | Olist data warehouse (portfolio) | done — 99 tests pass + 2 documented warns, CI green locally |
| 14 | Snowflake locally (fakesnow) + optional trial | todo |
| 17 | Election night live (TSE feed, near real time) | done — captured the 2026 runoff count live; 9 tests, CI |

Status values: todo → in progress (runs end to end, exercises open) → done.

## Notes for the next examples
- Versions checked on 2026-10-25: postgres 18.6, apache/kafka 4.3.1, debezium/connect 3.6.2.Final, dbt-core 1.12.6,
  dbt-duckdb 1.11.0, duckdb 1.5.6, dlt 1.31.0, confluent-kafka 2.16.0, pyspark 4.1.3 / delta-spark 4.4.1,
  apache/airflow 3.3.x, flink 2.x (java17), trinodb/trino 48x, apache/iceberg-rest-fixture 1.10.1, fakesnow 0.12.1.
- 06: bake Delta + hadoop-aws jars into the image at build time (no runtime downloads); MinIO via `pgsty/minio`.
- 09: Flink SQL with datagen/filesystem sources avoids extra connector jars; versioned views for temporal joins.
- 14: fakesnow has an HTTP server mode — test dbt-snowflake against it before designing the example.
