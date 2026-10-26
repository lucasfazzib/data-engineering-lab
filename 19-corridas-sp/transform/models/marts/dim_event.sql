-- Grain: one row per real-world event (entity-resolved across sources).
-- Survivorship: for each attribute, take the value from the most complete / most recent record.
with records as (
    select
        r.*,
        c.event_id,
        -- display name without payment-method suffixes ("... - Pix", "... - Cartão")
        trim(regexp_replace(r.name, '\s*-\s*(pix|cart[aã]o|boleto)\s*$', '', 'i')) as display_name
    from {{ ref('int_events__normalized') }} as r
    inner join {{ ref('int_er__clusters') }} as c using (record_key)
)

select
    event_id,
    -- the longest name tends to be the most descriptive version
    arg_max(display_name, length(display_name)) as event_name,
    min(event_date) as event_date,
    arg_max(start_time, start_time is not null) as start_time,
    any_value(ibge_code) as ibge_code,
    any_value(municipality) as municipality,
    list_sort(list_distinct(flatten(list(distance_categories)))) as distance_categories,
    min(price_brl) as price_from_brl,
    max(price_max_brl) as price_to_brl,
    -- most recent known status wins
    arg_max(status, fetched_at) filter (where status is not null) as status,
    arg_max(registration_url, fetched_at) filter (where registration_url is not null) as registration_url,
    count(*) as source_records,
    count(distinct source) as source_count,
    max(fetched_at) as last_seen_at
from records
group by event_id
