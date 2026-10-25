with source as (

    select * from {{ source('olist', 'sellers') }}

),

renamed as (

    select
        seller_id,
        lpad(seller_zip_code_prefix, 5, '0')    as zip_code_prefix,
        lower(trim(seller_city))                as city,
        upper(trim(seller_state))               as state_code

    from source

)

select * from renamed
