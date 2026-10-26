-- Which source records make up each event, with the original link (credit + traceability).
select
    c.event_id,
    r.record_key,
    r.source,
    r.source_event_id,
    r.name as source_name_of_event,
    r.source_url,
    r.fetched_at
from {{ ref('int_events__normalized') }} as r
inner join {{ ref('int_er__clusters') }} as c using (record_key)
