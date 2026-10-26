-- Grain: event x source record x version (from the SCD2 snapshot): price and status over time.
select
    c.event_id,
    s.record_key,
    s.source,
    s.price_brl,
    s.price_max_brl,
    s.status,
    s.event_date,
    s.dbt_valid_from as valid_from,
    s.dbt_valid_to as valid_to,
    s.dbt_valid_to is null as is_current,
    lag(s.price_brl) over (partition by s.record_key order by s.dbt_valid_from) as previous_price_brl,
    lag(s.status) over (partition by s.record_key order by s.dbt_valid_from) as previous_status
from {{ ref('snap_race_offer') }} as s
inner join {{ ref('int_er__clusters') }} as c using (record_key)
