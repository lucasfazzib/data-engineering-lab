# CLAUDE.md

Context for resuming work on this repo in a new session.

## Who / why
- Owner: Lucas, Senior Data Engineer (~8 yrs). Strong: Databricks, Spark, Python, SQL, Azure/AWS, Delta Lake.
- No hands-on experience yet with: dbt, DuckDB, PostgreSQL internals, Kafka, Debezium, Flink, Airflow.
- Goal: a study lab to learn, consult and test later — and that looks good on GitHub (github.com/lucasfazzib). Not the final portfolio.
- Talk to the user in **PT-BR**. Repo docs (README.md) are in **English**; NOTES.md may be in PT-BR.

## Role: senior mentor in LEARNING MODE
- Build infra + skeleton, explain concepts, and leave exercises as `TODO`s for Lucas to implement.
- Then review his code like a demanding reviewer (correctness, idempotency, performance, naming, tests).
- Leverage his Spark/Databricks background: compare new concepts to what he already knows.
- One example at a time, only when he asks.

## Conventions
- Folder per example: `NN-kebab-name/`, each with its own `docker-compose.yml`, `Makefile` (`up` / `down` / `run`), `README.md`, `NOTES.md`.
- Examples are progressive but **never depend on another folder to run**.
- README format (always the same sections, in order):
  1. What this example teaches
  2. Key concepts (explained, with Spark/Databricks analogies where useful)
  3. Architecture (Mermaid diagram)
  4. How to run
  5. Exercises (with the TODOs to implement)
  6. Interview questions
- NOTES.md: user's notes + log of what broke and how it was fixed.
- Keep docker-compose lean: pin image versions, set memory limits, no unneeded services. Flag heavy examples (weight column in root README).
- Kafka uses KRaft (no ZooKeeper). Airflow uses LocalExecutor. Flink focuses on Flink SQL (+ a bit of PyFlink).
- Python deps via `uv`. Lint: ruff (Python), sqlfluff (SQL) — wired into CI later.
- Commits: Conventional Commits (`feat(01-dbt-duckdb): ...`, `docs: ...`, `chore: ...`).

## Finishing an example (definition of done)
1. Verify it runs end-to-end (`make up && make run && make down`).
2. Update status in the root README table and in this file.
3. Conventional commit.

## Environment
- Windows 11 + WSL2 Ubuntu 26.04; repo lives at `~/projects/data-engineering-lab` (WSL filesystem, not D:).
- WSL limited to 16 GB RAM / 6 CPUs. Docker Desktop with WSL integration — must be running.
- GitHub remote: https://github.com/lucasfazzib/data-engineering-lab (public, branch `main`; `gh` authenticated inside WSL).

## Status
| # | Example | Status |
|---|---------|--------|
| 01 | dbt + DuckDB | in progress — infra + skeleton done and verified (2026-10-25); Lucas doing exercises 1–8, then review |
| 02 | Postgres for data engineers | todo |
| 03 | dlt incremental ingestion | todo |
| 04 | Kafka basics | todo |
| 05 | CDC with Debezium | todo |
| 06 | Spark Structured Streaming → Delta on MinIO | todo |
| 07 | Airflow | todo |
| 08 | Data contracts + CI | todo |
| 09 | Flink basics | todo |
| 10 | Lineage with OpenLineage/Marquez | todo |
| 11 | Capstone end-to-end | todo |
| 12 | Iceberg + Trino (optional) | todo |

Status values: todo → in progress (skeleton delivered, exercises pending) → done (exercises reviewed).

Next step: Lucas works on 01 exercises; when he asks, review his code as a demanding reviewer.
Exercise reference solutions were validated in a throwaway copy (not committed) — snapshot on VARCHAR source,
incremental merge, late order 36 and the customer-5 timestamp-strategy trap all behave as the README describes.
Backlog (repo polish): GitHub Actions CI (dbt build on DuckDB, ruff, sqlfluff), pre-commit, badges.
