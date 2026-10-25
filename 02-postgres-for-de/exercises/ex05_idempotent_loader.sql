-- EXERCISE 5 — an idempotent daily aggregate. Run with: make exercise N=05
\pset pager off

create table if not exists customer_daily_revenue (
    revenue_date date,
    customer_id  bigint,
    orders       int not null,
    revenue      numeric(14, 2) not null,
    primary key (revenue_date, customer_id)
);

-- TODO 1: write a statement that (re)computes ONE day (use a psql variable: \set day '2026-10-01')
--         from `orders` (delivered + shipped only) into customer_daily_revenue.
--         Running it twice must produce identical results.

-- TODO 2: implement it twice — once with INSERT ... ON CONFLICT and once with MERGE.
--         What does each version do with a customer whose orders for that day were all cancelled
--         AFTER the first run? (Hint: think about rows that must disappear.)

-- TODO 3: wrap the winner in a transaction and explain in NOTES.md why delete+insert-by-window
--         is the pattern most orchestrated pipelines (Airflow, dbt incremental) end up using.
