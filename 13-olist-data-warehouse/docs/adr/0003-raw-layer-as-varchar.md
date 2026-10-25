# ADR 0003 — Land raw data untouched, as VARCHAR

**Status:** accepted · **Date:** 2026-10-25

## Context
CSV type inference is a guess. Many readers (pandas, Spark `inferSchema`) parse zip prefixes like `01151`
as integers and silently drop the leading zero; inference can pick the wrong type from the first N rows,
and it changes behaviour between tool versions.

## Decision
`ingestion/extract_load.py` loads every column as VARCHAR, adds `_loaded_at` and `_source_file`, and
**validates the header against an expected column list** (the ingestion contract) before loading.
All casting happens in dbt staging models, where it is visible, reviewed and tested.

## Consequences
- Raw is a faithful, replayable copy of the source; a bad cast is fixed in SQL, not by re-ingesting.
- Schema drift in the source fails ingestion loudly instead of breaking a mart three layers later.
- Staging models are slightly more verbose (explicit `cast`s) — that verbosity is the documentation.
- Each run writes `warehouse/ingestion_manifest.json` (rows + sha256 per file) for reproducibility.
