-- One row per source record, normalized and placed on the map.
-- City -> official IBGE municipality (by name without accents) -> centroid coordinates.
-- Records outside SP, without a recognisable running format, or virtual are dropped here.
with events as (
    select * from {{ ref('stg_bronze__events') }}
),

municipalities as (
    select * from {{ ref('stg_reference__municipalities') }}
),

normalized as (
    select
        e.*,
        {{ normalize_name('e.name') }} as name_key,
        {{ normalize_city('e.city') }} as city_key,
        list_sort(list_distinct(e.distances_km)) as distances,
        list_sort(list_distinct(list_transform(e.distances_km, d -> {{ distance_category('d') }}))) as distance_categories
    from events as e
    where e.uf = 'SP'
      -- placeholder dates like 31/12/2050 exist in the source: races are announced months, not years, ahead
      and e.event_date <= current_date + interval 2 year
      -- CBAt also lists track and race-walking championships: from CBAt keep only road-running names
      and (
          e.source <> 'cbat'
          or regexp_matches(lower(strip_accents(e.name)), 'corrida|maratona|meia|run|milhas|\bkm\b|\d+k\b|rustica')
      )
      -- other sports and non-races listed on running platforms
      and not regexp_matches(
          lower(strip_accents(e.name)),
          'virtu|marcha atletica|pista|indoor|cross country|triathlon|duathlon|aquathlon|travessia|aguas abertas'
          || '|\bmtb\b|\bkids\b|curso|arbitragem'
      )
)

select
    n.record_key,
    n.source,
    n.source_event_id,
    n.source_url,
    n.name,
    n.name_key,
    n.event_date,
    n.start_time,
    n.city,
    n.city_key,
    m.ibge_code,
    m.municipality,
    m.lat,
    m.lon,
    n.distances,
    n.distance_categories,
    n.price_brl,
    n.price_max_brl,
    case when n.price_brl is not null and len(n.distances) > 0
        then round(n.price_brl / list_max(n.distances), 2) end as price_per_km_brl,
    n.status,
    n.registration_url,
    n.fetched_at
from normalized as n
left join municipalities as m on n.city_key = m.city_key
