-- Entity resolution, step 1: candidate pairs and their similarity score.
--
-- Blocking: only records on the same date (±1 day) in the same municipality are compared.
-- That turns an n² comparison into a handful of pairs and encodes the strongest rule we have:
-- two races in different cities or weeks are never the same event.
--
-- Score (0-1), weighted:
--   0.65  name similarity on the normalized name (payment variants, editions, years removed):
--         average of Jaro-Winkler (character level, tolerant to typos) and token Jaccard (shared words).
--         Jaro-Winkler alone is generous with short unrelated names; Jaccard is 0 when no word is shared.
--   0.20  distance overlap: Jaccard of the distance categories (unknown on either side = neutral 0.5)
--   0.15  same day (vs. ±1 day)
with r as (
    select * from {{ ref('int_events__normalized') }}
),

pairs as (
    select
        a.record_key as left_key,
        b.record_key as right_key,
        a.source as left_source,
        b.source as right_source,
        a.name as left_name,
        b.name as right_name,
        a.event_date as left_date,
        b.event_date as right_date,
        a.municipality,
        (
            jaro_winkler_similarity(a.name_key, b.name_key)
            + coalesce(
                len(list_intersect(string_split(a.name_key, ' '), string_split(b.name_key, ' ')))
                / nullif(len(list_distinct(list_concat(string_split(a.name_key, ' '), string_split(b.name_key, ' ')))), 0),
                0
            )
        ) / 2 as name_similarity,
        case
            when len(a.distance_categories) = 0 or len(b.distance_categories) = 0 then 0.5
            else len(list_intersect(a.distance_categories, b.distance_categories))
                / len(list_distinct(list_concat(a.distance_categories, b.distance_categories)))
        end as distance_overlap,
        a.event_date = b.event_date as same_day
    from r as a
    inner join r as b
        on a.record_key < b.record_key
        and a.ibge_code = b.ibge_code
        and abs(a.event_date - b.event_date) <= 1
)

select
    *,
    round(0.65 * name_similarity + 0.20 * distance_overlap + 0.15 * same_day::int, 4) as score,
    case
        when 0.65 * name_similarity + 0.20 * distance_overlap + 0.15 * same_day::int >= {{ var('er_auto_match') }}
            then 'match'
        when 0.65 * name_similarity + 0.20 * distance_overlap + 0.15 * same_day::int >= {{ var('er_review_min') }}
            then 'review'
        else 'distinct'
    end as decision
from pairs
