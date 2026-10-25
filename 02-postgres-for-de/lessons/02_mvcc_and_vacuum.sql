-- LESSON 02 — MVCC: why an UPDATE is really INSERT + "delete", and why VACUUM exists
\pset pager off
drop table if exists mvcc_demo;
create table mvcc_demo (id int primary key, val text) with (autovacuum_enabled = false, fillfactor = 100);
insert into mvcc_demo select g, 'v0' from generate_series(1, 100000) g;
analyze mvcc_demo;

\echo
\echo '== 1. Every row version carries xmin (creating txn) and xmax (deleting txn). ctid = physical location'
select ctid, xmin, xmax, * from mvcc_demo where id <= 3;

\echo
\echo '== 2. UPDATE writes a NEW tuple version (new ctid, new xmin). The old one becomes dead'
update mvcc_demo set val = 'v1' where id <= 3;
select ctid, xmin, xmax, * from mvcc_demo where id <= 3;

\echo
\echo '== 3. Mass update: table size doubles, dead tuples pile up (autovacuum disabled on purpose)'
select pg_size_pretty(pg_relation_size('mvcc_demo')) as size_before;
update mvcc_demo set val = 'v2';
select pg_sleep(1); -- give the cumulative stats a moment to flush
select n_dead_tup, pg_size_pretty(pg_relation_size('mvcc_demo')) as size_after
from pg_stat_user_tables where relname = 'mvcc_demo';

\echo
\echo '== 4. VACUUM marks dead space as reusable (size does NOT shrink). VACUUM FULL rewrites the table (exclusive lock!)'
vacuum mvcc_demo;
select pg_sleep(1);
select n_dead_tup, pg_size_pretty(pg_relation_size('mvcc_demo')) as after_vacuum
from pg_stat_user_tables where relname = 'mvcc_demo';
vacuum full mvcc_demo;
select pg_size_pretty(pg_relation_size('mvcc_demo')) as after_vacuum_full;

\echo
\echo '== 5. HOT updates: with free space in the page (fillfactor < 100) and no indexed column changed,'
\echo '      Postgres updates without touching indexes. Compare n_tup_upd vs n_tup_hot_upd'
alter table mvcc_demo set (fillfactor = 70);
vacuum full mvcc_demo;
select pg_stat_reset_single_table_counters('mvcc_demo'::regclass);
update mvcc_demo set val = 'v3' where id <= 20000;
select pg_sleep(1);
select n_tup_upd, n_tup_hot_upd from pg_stat_user_tables where relname = 'mvcc_demo';

\echo
\echo '== 6. Long-running transactions block cleanup: VACUUM cannot remove tuples still visible to'
\echo '      the oldest open snapshot. Check for them with:'
select pid, state, xact_start, backend_xmin, left(query, 60) as query
from pg_stat_activity where backend_xmin is not null order by xact_start limit 5;

drop table mvcc_demo;
