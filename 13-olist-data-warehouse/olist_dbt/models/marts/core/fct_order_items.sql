-- Grain: one row per order line. Use it for product/seller/category analysis.
with items as (

    select * from {{ ref('stg_olist__order_items') }}

),

orders as (

    select
        order_id,
        customer_key,
        purchase_date_key,
        order_status,
        is_sale
    from {{ ref('fct_orders') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['items.order_id', 'items.order_item_number']) }} as order_item_key,
    items.order_id,
    items.order_item_number,
    {{ dbt_utils.generate_surrogate_key(['items.product_id']) }}     as product_key,
    {{ dbt_utils.generate_surrogate_key(['items.seller_id']) }}      as seller_key,
    orders.customer_key,
    orders.purchase_date_key,
    orders.order_status,
    orders.is_sale,
    items.shipping_limit_at,
    items.price,
    items.freight_value

from items
inner join orders on items.order_id = orders.order_id
