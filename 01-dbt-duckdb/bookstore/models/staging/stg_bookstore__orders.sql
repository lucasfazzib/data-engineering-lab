-- raw.orders is append-only: each status change lands as a new row.
-- Staging keeps only the LATEST version of each order (same idea as a Delta MERGE source dedup).
with source as (

    select * from {{ source('bookstore', 'orders') }}

),

renamed as (

    select
        cast(order_id as integer)       as order_id,
        cast(customer_id as integer)    as customer_id,
        status,
        cast(ordered_at as timestamp)   as ordered_at,
        cast(updated_at as timestamp)   as updated_at,
        _loaded_at

    from source

),

latest as (

    select *
    from renamed
    qualify row_number() over (partition by order_id order by updated_at desc, _loaded_at desc) = 1

)

select * from latest
