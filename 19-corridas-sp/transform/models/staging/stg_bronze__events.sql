-- Latest version of every record, all sources stacked (same contract: corridas.sources.base.RaceRecord).
-- Bronze keeps one file per collection day; here we keep the newest observation per source record.
with stacked as (
    select * from {{ source('bronze', 'cbat') }}
    union all by name
    select * from {{ source('bronze', 'minhas_inscricoes') }}
)

select
    source || ':' || source_event_id as record_key,
    source,
    source_event_id,
    source_url,
    trim(name) as name,
    event_date,
    nullif(trim(city), '') as city,
    upper(uf) as uf,
    start_time,
    distances_km,
    price_brl,
    price_max_brl,
    status,
    registration_url,
    fetched_at,
    content_hash
from stacked
qualify row_number() over (partition by source, source_event_id order by fetched_at desc) = 1
