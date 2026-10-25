# ADR 0001 — DuckDB as the local warehouse

**Status:** accepted · **Date:** 2026-10-25

## Context
The project must run on a laptop at zero cost, be reproducible by anyone who clones it, and still exercise
real warehouse patterns (layered models, star schema, tests, contracts, CI). Data volume: ~1.5M rows in total.

## Options
| Option | Pros | Cons |
|---|---|---|
| **DuckDB** (file) | zero infra, columnar + vectorized, fast on 1-100M rows, first-class dbt adapter, runs in CI | single writer, not a shared multi-user service |
| Postgres in Docker | familiar, multi-user | row store: slow analytical scans, one more service to run |
| Snowflake / BigQuery / Databricks | the real production targets | cost, credentials, not reproducible for someone cloning the repo |

## Decision
DuckDB, accessed only through dbt (transformations) and read-only connections (dashboard).

## Consequences
- The SQL is close to ANSI and to Snowflake/Databricks SQL; moving to a cloud warehouse means changing the
  dbt profile and a few functions (`arg_max`, `median`, `mode`, `strftime`).
- Only one process can write at a time: don't run `dbt build` while the dashboard holds a connection
  (the dashboard opens read-only, short-lived connections to minimize this).
- CI can build the whole project (`dbt build --empty`) in seconds with no secrets.
