-- LESSON 04 — declarative partitioning, partition pruning and cheap retention
\pset pager off
drop table if exists events cascade;

\echo
\echo '== 1. Range-partitioned parent table (holds no data itself)'
create table events (
    event_id   bigint generated always as identity,
    event_time timestamptz not null,
    user_id    bigint not null,
    event_type text not null,
    primary key (event_id, event_time) -- the partition key must be part of every unique constraint
) partition by range (event_time);

-- one partition per month for the last 6 months + a default partition
do $$
declare m date := date_trunc('month', now() - interval '5 months');
begin
    while m <= date_trunc('month', now()) loop
        execute format(
            'create table events_%s partition of events for values from (%L) to (%L)',
            to_char(m, 'YYYY_MM'), m, (m + interval '1 month')::date);
        m := m + interval '1 month';
    end loop;
end $$;
create table events_default partition of events default;

insert into events (event_time, user_id, event_type)
select date_trunc('month', now() - interval '5 months') + random() * (now() - date_trunc('month', now() - interval '5 months')),
       floor(random() * 10000), (array['view', 'click', 'purchase'])[1 + floor(random() * 3)::int]
from generate_series(1, 300000);
create index on events (user_id); -- creates a matching index on every partition
analyze events;

\echo
\echo '== 2. Rows per partition'
select tableoid::regclass as partition, count(*) from events group by 1 order by 1;

\echo
\echo '== 3. Partition pruning: filter on the partition key -> only one partition is scanned'
explain (costs off) select count(*) from events where event_time >= date_trunc('month', now());
\echo '   ("Subplans Removed" = pruned at execution time, because now() is not a constant at plan time.'
\echo '    The default partition is kept: it could hold any future timestamp.)'

\echo
\echo '== 4. No filter on the partition key -> every partition is scanned'
explain (costs off) select count(*) from events where user_id = 42;

\echo
\echo '== 5. Retention: DROP/DETACH a partition is instant; DELETE would scan, write WAL and leave dead tuples'
select tableoid::regclass as oldest from events order by event_time limit 1 \gset
alter table events detach partition :oldest;
drop table :oldest;
select tableoid::regclass as partition, count(*) from events group by 1 order by 1;

\echo
\echo '== 6. Rows outside every range land in the default partition (monitor it: it should stay empty)'
insert into events (event_time, user_id, event_type) values (now() + interval '2 years', 1, 'view');
select count(*) as rows_in_default from events_default;
