# ADR 0002 — Kimball star schema with an analytics layer on top

**Status:** accepted · **Date:** 2026-10-25

## Context
Consumers are BI dashboards and analysts asking business questions (sales trend, delivery performance,
seller concentration, retention). The source is a normalized OLTP-like export with 9 tables.

## Options
- **One Big Table** per use case: simplest to query, duplicates logic across tables, hard to keep consistent.
- **Data Vault**: great for many sources and full auditability; overkill for one static source.
- **Kimball star schema** (conformed dimensions + facts at explicit grains), with a thin layer of
  question-specific marts on top.

## Decision
Kimball. Layers: `staging` (1:1 with sources) → `intermediate` (reusable logic) → `core` (`dim_*`, `fct_*`)
→ `analytics` (`mart_*`).

- **Grains are explicit** and tested: `fct_orders` = 1 row per order, `fct_order_items` = 1 row per order line.
- **Surrogate keys** (hash of the natural key, `dbt_utils.generate_surrogate_key`) on every dimension,
  so a future change of source/natural key does not ripple into facts.
- **Customer = `customer_unique_id`**, not `customer_id` (which Olist regenerates per order).
- **Order-time attributes live on the fact** (delivery state/zip), current attributes on the dimension
  (customer's latest address): the analysis "where did we deliver?" must not change when a customer moves.
- **Pre-aggregate before joining** (`int_order_items__by_order`, `int_order_payments__by_order`) to avoid
  the fan-out trap of joining two one-to-many tables to orders.

## Consequences
- New questions usually need only a new `mart_*` built from `core`.
- Dimensions are SCD type 1 (static dataset). With a live source, `dim_customers` would be built on a dbt
  snapshot (SCD2) — see example 01 of this repo.
