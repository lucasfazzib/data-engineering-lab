-- One row per real customer (customer_unique_id). Address = the one used in the customer's latest order.
with customers as (

    select * from {{ ref('stg_olist__customers') }}

),

orders as (

    select
        order_id,
        customer_id,
        purchased_at
    from {{ ref('stg_olist__orders') }}

),

states as (

    select * from {{ ref('br_states') }}

),

centroids as (

    select * from {{ ref('int_geolocation__zip_centroids') }}

),

customer_orders as (

    select
        customers.customer_unique_id,
        customers.zip_code_prefix,
        customers.city,
        customers.state_code,
        orders.order_id,
        orders.purchased_at
    from customers
    inner join orders on customers.customer_id = orders.customer_id

),

latest_address as (

    select
        customer_unique_id,
        zip_code_prefix,
        city,
        state_code
    from customer_orders
    qualify row_number() over (partition by customer_unique_id order by purchased_at desc, order_id asc) = 1

),

order_stats as (

    select
        customer_unique_id,
        min(purchased_at)           as first_order_at,
        max(purchased_at)           as last_order_at,
        count(distinct order_id)    as lifetime_orders
    from customer_orders
    group by customer_unique_id

)

select
    {{ dbt_utils.generate_surrogate_key(['latest_address.customer_unique_id']) }} as customer_key,
    latest_address.customer_unique_id,
    latest_address.zip_code_prefix,
    latest_address.city,
    latest_address.state_code,
    states.state_name,
    states.region,
    centroids.latitude,
    centroids.longitude,
    order_stats.first_order_at,
    order_stats.last_order_at,
    order_stats.lifetime_orders,
    order_stats.lifetime_orders > 1 as is_repeat_customer

from latest_address
inner join order_stats on latest_address.customer_unique_id = order_stats.customer_unique_id
left join states on latest_address.state_code = states.state_code
left join centroids on latest_address.zip_code_prefix = centroids.zip_code_prefix
