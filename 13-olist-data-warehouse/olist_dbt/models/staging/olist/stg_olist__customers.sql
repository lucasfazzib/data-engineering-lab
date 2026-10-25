with source as (

    select * from {{ source('olist', 'customers') }}

),

renamed as (

    select
        customer_id,
        customer_unique_id,
        lpad(customer_zip_code_prefix, 5, '0') as zip_code_prefix,
        lower(trim(customer_city))             as city,
        upper(trim(customer_state))            as state_code

    from source

)

select * from renamed
