-- Grain: one row per order. Items and payments are pre-aggregated to order grain (no fan-out).
with orders as (

    select * from {{ ref('stg_olist__orders') }}

),

customers as (

    select * from {{ ref('stg_olist__customers') }}

),

items as (

    select * from {{ ref('int_order_items__by_order') }}

),

payments as (

    select * from {{ ref('int_order_payments__by_order') }}

),

reviews as (

    select * from {{ ref('int_order_reviews__latest') }}

)

select
    orders.order_id,
    {{ dbt_utils.generate_surrogate_key(['customers.customer_unique_id']) }}     as customer_key,
    cast(strftime(orders.purchased_at, '%Y%m%d') as integer)                    as purchase_date_key,
    orders.order_status,
    -- the delivery address belongs to the order (the customer may move later): degenerate attributes
    customers.zip_code_prefix                                                   as delivery_zip_code_prefix,
    customers.state_code                                                        as delivery_state_code,

    orders.purchased_at,
    orders.approved_at,
    orders.delivered_to_carrier_at,
    orders.delivered_to_customer_at,
    orders.estimated_delivery_at,

    cast(coalesce(items.item_count, 0) as integer)                              as item_count,
    cast(coalesce(items.seller_count, 0) as integer)                            as seller_count,
    cast(coalesce(items.items_value, 0) as decimal(14, 2))                      as items_value,
    cast(coalesce(items.freight_value, 0) as decimal(14, 2))                    as freight_value,
    cast(coalesce(items.items_value, 0) + coalesce(items.freight_value, 0) as decimal(14, 2)) as order_value,
    cast(coalesce(payments.payment_value, 0) as decimal(14, 2))                 as payment_value,
    cast(coalesce(payments.payment_count, 0) as integer)                        as payment_count,
    payments.max_installments,
    payments.primary_payment_type,
    coalesce(payments.used_voucher, false)                                      as used_voucher,
    reviews.review_score,

    orders.order_status in ('{{ var("sale_statuses") | join("', '") }}')        as is_sale,
    orders.delivered_to_customer_at is not null                                 as is_delivered,
    date_diff('day', orders.purchased_at, orders.delivered_to_customer_at)      as delivery_days,
    date_diff('day', orders.purchased_at, orders.estimated_delivery_at)         as estimated_delivery_days,
    case
        when orders.delivered_to_customer_at is null then null
        else cast(orders.delivered_to_customer_at as date) > cast(orders.estimated_delivery_at as date)
    end                                                                         as is_late

from orders
inner join customers on orders.customer_id = customers.customer_id
left join items on orders.order_id = items.order_id
left join payments on orders.order_id = payments.order_id
left join reviews on orders.order_id = reviews.order_id
