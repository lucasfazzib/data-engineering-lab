-- EXERCISE 1 — query tuning. Run with: make exercise N=01
-- Start from a clean state: drops the indexes created by lesson 01.
\pset pager off
drop index if exists ix_orders_customer, ix_orders_customer_created, ix_orders_created_brin,
    ix_customers_lower_email, ix_orders_open, ix_orders_attributes, ix_orders_customer_incl;

-- The "customer orders page" query. Product wants it under 1 ms.
explain (analyze, buffers)
select order_id, status, amount, created_at
from orders
where customer_id = 777
  and status <> 'cancelled'
order by created_at desc
limit 20;

-- TODO 1: create the index that makes this query fast. Justify column order in NOTES.md.
-- TODO 2: does INCLUDE help here? Try it and compare "Heap Fetches" and buffers.
-- TODO 3: why can't Postgres use a regular index for `status <> 'cancelled'` efficiently?
--         Would a partial index help? Measure it.
