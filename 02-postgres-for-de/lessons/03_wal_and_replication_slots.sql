-- LESSON 03 — WAL and logical replication slots (the foundation of CDC / Debezium)
\pset pager off
select pg_drop_replication_slot(slot_name) from pg_replication_slots where slot_name = 'lesson_slot';
drop table if exists wal_demo;

\echo
\echo '== 1. Every change is first written to the WAL. LSN = position in the WAL stream'
show wal_level;
select pg_current_wal_lsn() as lsn_now, pg_walfile_name(pg_current_wal_lsn()) as wal_file;

\echo
\echo '== 2. Measuring how much WAL a statement generates'
create table wal_demo (id int primary key, name text, amount numeric);
select pg_current_wal_lsn() as before_lsn \gset
insert into wal_demo select g, 'name ' || g, g * 1.5 from generate_series(1, 50000) g;
select pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), :'before_lsn')) as wal_generated_by_insert;

\echo
\echo '== 3. A logical replication slot decodes WAL into row changes. test_decoding = human-readable plugin'
\echo '      (Debezium uses pgoutput, the built-in plugin for logical replication)'
select slot_name, lsn from pg_create_logical_replication_slot('lesson_slot', 'test_decoding');

insert into wal_demo values (100001, 'new row', 10);
update wal_demo set amount = 99 where id = 1;
delete from wal_demo where id = 2;

\echo
\echo '== 4. Peek the decoded changes (peek does NOT advance the slot). Note: UPDATE/DELETE only carry the PK'
select lsn, xid, data from pg_logical_slot_peek_changes('lesson_slot', null, null);

\echo
\echo '== 5. get_changes CONSUMES the changes and advances confirmed_flush_lsn (a consumer "acks" them)'
select confirmed_flush_lsn as before_ack from pg_replication_slots where slot_name = 'lesson_slot';
select count(*) as consumed from pg_logical_slot_get_changes('lesson_slot', null, null);
select confirmed_flush_lsn as after_ack from pg_replication_slots where slot_name = 'lesson_slot';

\echo
\echo '== 6. REPLICA IDENTITY FULL: old values of every column are logged (what CDC needs to emit "before")'
alter table wal_demo replica identity full;
update wal_demo set amount = 7 where id = 3;
delete from wal_demo where id = 4;
select data from pg_logical_slot_get_changes('lesson_slot', null, null);

\echo
\echo '== 7. THE classic CDC incident: an inactive slot pins WAL forever and fills the disk.'
\echo '      Generate WAL without consuming the slot and watch retained_wal grow:'
insert into wal_demo select g, 'more', g from generate_series(200000, 260000) g;
select slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as retained_wal
from pg_replication_slots;
\echo '      Mitigation: monitor this lag, set max_slot_wal_keep_size, drop abandoned slots.'
show max_slot_wal_keep_size;

select pg_drop_replication_slot('lesson_slot');
drop table wal_demo;
