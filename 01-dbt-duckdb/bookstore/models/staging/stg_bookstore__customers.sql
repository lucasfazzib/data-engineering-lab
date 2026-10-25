-- Staging = 1:1 with a source table. Only rename, cast, clean. No joins, no business logic.
with source as (

    select * from {{ source('bookstore', 'customers') }}

),

renamed as (

    select
        cast(customer_id as integer)            as customer_id,
        first_name,
        last_name,
        first_name || ' ' || last_name           as full_name,
        lower(trim(email))                       as email,
        upper(trim(country_code))                as country_code,
        tier,
        cast(created_at as timestamp)            as created_at,
        cast(updated_at as timestamp)            as updated_at,
        _loaded_at

    from source

)

select * from renamed
