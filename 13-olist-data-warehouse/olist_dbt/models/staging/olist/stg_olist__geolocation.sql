with source as (

    select * from {{ source('olist', 'geolocation') }}

),

renamed as (

    select
        lpad(geolocation_zip_code_prefix, 5, '0')   as zip_code_prefix,
        cast(geolocation_lat as double)             as latitude,
        cast(geolocation_lng as double)             as longitude,
        lower(trim(geolocation_city))               as city,
        upper(trim(geolocation_state))              as state_code

    from source

)

select * from renamed
