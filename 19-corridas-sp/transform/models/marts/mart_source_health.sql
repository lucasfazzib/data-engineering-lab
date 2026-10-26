-- Is each scraper still working? A layout change usually shows up as fewer records or emptier fields,
-- not as an error. Compare the latest run with the median of the previous runs.
with runs as (
    select
        source,
        finished_at,
        records,
        errors,
        row_number() over (partition by source order by finished_at desc) as run_rank
    from {{ ref('stg_bronze__runs') }}
),

latest as (
    select * from runs where run_rank = 1
),

baseline as (
    select source, median(records) as median_records, count(*) as previous_runs
    from runs
    where run_rank between 2 and 8
    group by source
),

fill as (
    select
        source,
        round(avg((len(distances_km) > 0)::int), 3) as pct_with_distances,
        round(avg((price_brl is not null)::int), 3) as pct_with_price,
        round(avg((status is not null)::int), 3) as pct_with_status
    from {{ ref('stg_bronze__events') }}
    group by source
)

select
    l.source,
    l.finished_at as last_run_at,
    l.records as last_run_records,
    b.median_records as previous_median_records,
    coalesce(b.previous_runs, 0) as previous_runs,
    l.errors as last_error,
    f.pct_with_distances,
    f.pct_with_price,
    f.pct_with_status,
    case
        when l.errors is not null then 'error'
        when l.records = 0 then 'empty'
        when b.median_records > 0 and l.records < 0.5 * b.median_records then 'volume_drop'
        else 'ok'
    end as health
from latest as l
left join baseline as b using (source)
left join fill as f using (source)
