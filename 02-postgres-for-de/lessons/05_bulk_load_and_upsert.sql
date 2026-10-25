-- LESSON 05 — loading data like a data engineer: COPY, idempotent upserts, MERGE
\pset pager off
drop table if exists daily_sales, staging_sales;

create table daily_sales (
    sale_date date,
    store_id  int,
    revenue   numeric(12, 2) not null,
    loaded_at timestamptz not null default now(),
    primary key (sale_date, store_id)
);
create unlogged table staging_sales (sale_date date, store_id int, revenue numeric(12, 2));

\echo
\echo '== 1. Row-by-row INSERT vs COPY (200k rows each)'
\timing on
do $$ begin for i in 1..200000 loop insert into staging_sales values (current_date, i, i); end loop; end $$;
truncate staging_sales;
copy (select current_date - (g % 30), g % 500, round((random() * 1000)::numeric, 2) from generate_series(1, 200000) g)
    to '/tmp/sales.csv' with (format csv);
copy staging_sales from '/tmp/sales.csv' with (format csv);
\timing off
\echo '   The loop runs INSIDE the server, so it pays no network cost — and COPY still wins.'
\echo '   From a client (Python, JDBC) row-by-row INSERT pays one round trip per row: COPY is 10-100x faster.'

\echo
\echo '== 2. Idempotent load with INSERT ... ON CONFLICT: running it twice gives the same result'
insert into daily_sales (sale_date, store_id, revenue)
select sale_date, store_id, sum(revenue) from staging_sales group by 1, 2
on conflict (sale_date, store_id) do update set revenue = excluded.revenue, loaded_at = now();
select count(*) as rows_after_first_load, sum(revenue) from daily_sales;

insert into daily_sales (sale_date, store_id, revenue)
select sale_date, store_id, sum(revenue) from staging_sales group by 1, 2
on conflict (sale_date, store_id) do update set revenue = excluded.revenue, loaded_at = now();
select count(*) as rows_after_second_load, sum(revenue) from daily_sales;

\echo
\echo '== 3. MERGE (PG15+, with RETURNING since PG17): insert, update and delete in one statement'
truncate staging_sales;
-- one existing key with revenue 0 (-> delete), one existing key with a new value (-> update), one new key (-> insert)
insert into staging_sales
select sale_date, store_id, case when rn = 1 then 0 else 123.45 end
from (select sale_date, store_id, row_number() over (order by sale_date, store_id) as rn
      from daily_sales order by sale_date, store_id limit 2) existing
union all
select current_date + 1, 1, 50;
merge into daily_sales t
using staging_sales s on t.sale_date = s.sale_date and t.store_id = s.store_id
when matched and s.revenue = 0 then delete
when matched then update set revenue = s.revenue, loaded_at = now()
when not matched then insert (sale_date, store_id, revenue) values (s.sale_date, s.store_id, s.revenue)
returning merge_action(), t.sale_date, t.store_id, t.revenue;

\echo
\echo '== 4. Delete + insert by partition window (the pattern Airflow DAGs use for idempotent daily runs)'
begin;
delete from daily_sales where sale_date = current_date - 1;
insert into daily_sales (sale_date, store_id, revenue) values (current_date - 1, 1, 10), (current_date - 1, 2, 20);
commit;
select sale_date, count(*) from daily_sales where sale_date >= current_date - 1 group by 1 order by 1;

drop table daily_sales, staging_sales;
