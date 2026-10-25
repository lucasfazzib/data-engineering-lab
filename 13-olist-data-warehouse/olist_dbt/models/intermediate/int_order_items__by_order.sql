-- Order lines rolled up to order grain, BEFORE joining to orders (avoids fan-out when joined with payments).
with items as (

    select * from {{ ref('stg_olist__order_items') }}

)

select
    order_id,
    count(*)                    as item_count,
    count(distinct product_id)  as distinct_products,
    count(distinct seller_id)   as seller_count,
    sum(price)                  as items_value,
    sum(freight_value)          as freight_value

from items
group by order_id
