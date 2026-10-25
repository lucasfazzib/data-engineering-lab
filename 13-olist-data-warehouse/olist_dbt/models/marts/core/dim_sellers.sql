with sellers as (

    select * from {{ ref('stg_olist__sellers') }}

),

states as (

    select * from {{ ref('br_states') }}

),

centroids as (

    select * from {{ ref('int_geolocation__zip_centroids') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['sellers.seller_id']) }} as seller_key,
    sellers.seller_id,
    sellers.zip_code_prefix,
    sellers.city,
    sellers.state_code,
    states.state_name,
    states.region,
    centroids.latitude,
    centroids.longitude

from sellers
left join states on sellers.state_code = states.state_code
left join centroids on sellers.zip_code_prefix = centroids.zip_code_prefix
