-- LESSON 01 — reading EXPLAIN and choosing indexes
-- Idempotent: drops what it creates, so it can be re-run.
\pset pager off
drop index if exists ix_orders_customer, ix_orders_customer_created, ix_orders_created_brin,
    ix_customers_lower_email, ix_orders_open, ix_orders_attributes, ix_orders_customer_incl;

\echo
\echo '== 1. No index on customer_id: Seq Scan reads the whole table (look at Buffers: shared hit/read)'
explain (analyze, buffers) select * from orders where customer_id = 4242;

\echo
\echo '== 2. B-tree on customer_id: Index Scan / Bitmap Heap Scan'
create index ix_orders_customer on orders (customer_id);
explain (analyze, buffers) select * from orders where customer_id = 4242;

\echo
\echo '== 3. Composite index (customer_id, created_at): equality column FIRST, range column second'
create index ix_orders_customer_created on orders (customer_id, created_at);
explain (analyze, buffers)
select order_id, created_at from orders
where customer_id = 4242 and created_at >= now() - interval '90 days';

\echo
\echo '== 4. Covering index with INCLUDE -> Index Only Scan (no heap access, check "Heap Fetches")'
vacuum (analyze) orders; -- index-only scans need an up-to-date visibility map
create index ix_orders_customer_incl on orders (customer_id) include (amount);
explain (analyze, buffers) select sum(amount) from orders where customer_id = 4242;

\echo
\echo '== 5. Low selectivity: an index on status would NOT help "status = delivered" (~50% of rows)'
explain select count(*) from orders where status = 'delivered';

\echo
\echo '== 6. Partial index: only the rows you query often (small and cheap to maintain)'
create index ix_orders_open on orders (created_at) where status in ('placed', 'shipped');
explain (analyze, buffers)
select count(*) from orders where status = 'placed' and created_at >= now() - interval '7 days';

\echo
\echo '== 7. Expression index: WHERE lower(email) = ... cannot use a plain index on email'
create index ix_customers_lower_email on customers (lower(email));
explain (analyze) select * from customers where lower(email) = 'user123@example.com';

\echo
\echo '== 8. BRIN: tiny index for naturally ordered, append-only columns (created_at here)'
create index ix_orders_created_brin on orders using brin (created_at);
explain (analyze, buffers)
select count(*) from orders where created_at between now() - interval '2 days' and now() - interval '1 day';

\echo
\echo '== 9. GIN on jsonb: containment queries (@>)'
create index ix_orders_attributes on orders using gin (attributes jsonb_path_ops);
explain (analyze) select count(*) from orders where attributes @> '{"coupon": "PROMO3"}';

\echo
\echo '== 10. Index sizes: compare BRIN vs B-tree on the same table'
select indexrelname as index, pg_size_pretty(pg_relation_size(indexrelid)) as size
from pg_stat_user_indexes where relname in ('orders', 'customers') order by pg_relation_size(indexrelid) desc;
