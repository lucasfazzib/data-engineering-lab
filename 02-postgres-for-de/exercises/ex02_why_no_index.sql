-- EXERCISE 2 — "I created the index but Postgres ignores it". Run with: make exercise N=02
\pset pager off
create index if not exists ix_ex02_created on orders (created_at);
create index if not exists ix_ex02_email on customers (email);

-- Each query below does NOT use the index the way you would expect.
-- TODO: for each one, explain why in NOTES.md and rewrite it (or create a better index) so it does.

-- a) function on the indexed column
explain select count(*) from orders where date(created_at) = current_date - 10;

-- b) case-insensitive search
explain select * from customers where email ilike 'USER42@EXAMPLE.COM';

-- c) leading wildcard
explain select * from customers where email like '%42@example.com';

-- d) the planner thinks the index is not worth it — when is that the right call?
explain select * from orders where created_at > now() - interval '300 days';
