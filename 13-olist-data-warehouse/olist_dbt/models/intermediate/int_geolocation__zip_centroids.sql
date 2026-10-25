-- The source has ~50 coordinates per zip prefix, some of them outside Brazil.
-- Keep one representative point per prefix: the median of the coordinates inside Brazil's bounding box.
with geolocation as (

    select * from {{ ref('stg_olist__geolocation') }}

),

inside_brazil as (

    select *
    from geolocation
    where
        latitude between -33.75 and 5.27
        and longitude between -73.99 and -34.79

)

select
    zip_code_prefix,
    median(latitude)        as latitude,
    median(longitude)       as longitude,
    mode(state_code)        as state_code,
    count(*)                as source_points

from inside_brazil
group by zip_code_prefix
