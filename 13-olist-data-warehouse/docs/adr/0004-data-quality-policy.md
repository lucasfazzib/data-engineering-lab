# ADR 0004 — Data quality policy: what blocks a build and what only warns

**Status:** accepted · **Date:** 2026-10-25

## Context
Real data has known defects. If every defect fails the build, people learn to ignore failures;
if nothing fails, broken data reaches the dashboard.

## Decision
| Check | Where | Severity |
|---|---|---|
| Primary keys unique + not null | every model | **error** |
| Foreign keys (`relationships`) between facts and dimensions | core | **error** |
| Accepted values (status, payment type, region) | staging / seeds | **error** |
| Ranges (price > 0, review 1–5, retention 0–1) | staging / analytics | **error** |
| Model contracts (column names + types) | `fct_orders`, `dim_customers` | **error** at build time |
| Business-logic unit tests (dedup, payment roll-up) | intermediate | **error** (run in CI) |
| Known source anomalies (payments ≠ items + freight, delivered without date) | core | **warn**, failing rows stored |

All tests use `store_failures: true`: failing rows are written to the `audit` schema so the investigation
starts with a `select`, not with re-running SQL by hand.

## Consequences
- A red build always means something new and actionable.
- Warnings are documented in the README with their counts; a change in those counts is a signal.
- In production, warn-level results would be sent to an alerting channel and tracked over time.
