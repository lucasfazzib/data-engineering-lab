-- EXERCISE 4 — migrate `orders` (1M rows, not partitioned) to a monthly-partitioned table.
-- Run with: make exercise N=04
\pset pager off

-- TODO 1: create orders_partitioned (same columns) partitioned by range on created_at, one partition per month.
--         Note the primary key problem: what has to change?

-- TODO 2: copy the data in batches (not one giant INSERT). Why batches?

-- TODO 3: swap the tables with renames inside a single transaction.

-- TODO 4: prove partition pruning works on the new table with EXPLAIN.

-- TODO 5 (NOTES.md only): how would you do this on a live production table receiving writes 24/7?
--         (hint: triggers / dual writes / logical replication into the new table)
