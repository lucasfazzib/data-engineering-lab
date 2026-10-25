with source as (

    select * from {{ source('olist', 'order_items') }}

),

renamed as (

    select
        order_id,
        cast(order_item_id as integer)              as order_item_number,
        product_id,
        seller_id,
        cast(shipping_limit_date as timestamp)      as shipping_limit_at,
        cast(price as decimal(12, 2))               as price,
        cast(freight_value as decimal(12, 2))       as freight_value

    from source

)

select * from renamed
