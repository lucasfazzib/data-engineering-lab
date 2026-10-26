-- What the app shows: future events in SP, one row per event, with location and source links.
select
    e.event_id,
    e.event_name,
    e.event_date,
    dayname(e.event_date) as weekday,
    e.start_time,
    e.municipality,
    l.lat,
    l.lon,
    e.distance_categories,
    e.price_from_brl,
    e.price_to_brl,
    e.status,
    e.registration_url,
    e.source_count,
    (
        select list(distinct s.source_name order by s.source_name)
        from {{ ref('bridge_event_source') }} as b
        inner join {{ ref('sources') }} as s on b.source = s.source
        where b.event_id = e.event_id
    ) as sources
from {{ ref('dim_event') }} as e
left join {{ ref('dim_location') }} as l on e.ibge_code = l.ibge_code
where e.event_date >= current_date
