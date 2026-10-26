-- Grain: event x distance (a 5k and a 10k on the same morning are two races of one event).
with exploded as (
    select distinct
        c.event_id,
        unnest(r.distances) as distance_km
    from {{ ref('int_events__normalized') }} as r
    inner join {{ ref('int_er__clusters') }} as c using (record_key)
)

select
    event_id || ':' || distance_km as race_id,
    event_id,
    distance_km,
    {{ distance_category('distance_km') }} as distance_category
from exploded
