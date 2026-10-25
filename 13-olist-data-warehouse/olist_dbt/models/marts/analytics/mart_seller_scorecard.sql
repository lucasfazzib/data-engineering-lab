-- One row per seller: volume, quality and a Pareto segment (which sellers make 80% of GMV).
with items as (

    select * from {{ ref('fct_order_items') }}
    where is_sale

),

orders as (

    select
        order_id,
        review_score,
        is_late,
        delivery_days,
        purchased_at
    from {{ ref('fct_orders') }}

),

sellers as (

    select * from {{ ref('dim_sellers') }}

),

seller_orders as (

    -- one row per (seller, order): an order with 2 items from the same seller counts once for quality metrics
    select
        items.seller_key,
        items.order_id,
        sum(items.price)        as gmv,
        count(*)                as items
    from items
    group by 1, 2

),

per_seller as (

    select
        seller_orders.seller_key,
        count(*)                                                        as orders,
        sum(seller_orders.items)                                        as items_sold,
        sum(seller_orders.gmv)                                          as gmv,
        avg(orders.review_score)                                        as avg_review_score,
        avg(case when orders.is_late then 1.0 when not orders.is_late then 0.0 end) as late_delivery_rate,
        avg(orders.delivery_days)                                       as avg_delivery_days,
        min(orders.purchased_at)                                        as first_sale_at,
        max(orders.purchased_at)                                        as last_sale_at
    from seller_orders
    inner join orders on seller_orders.order_id = orders.order_id
    group by 1

),

ranked as (

    select
        *,
        rank() over (order by gmv desc)                                         as gmv_rank,
        sum(gmv) over (order by gmv desc, seller_key asc rows unbounded preceding)
        / sum(gmv) over ()                                                  as cumulative_gmv_share
    from per_seller

)

select
    ranked.seller_key,
    sellers.seller_id,
    sellers.state_code,
    sellers.region,
    ranked.orders,
    ranked.items_sold,
    ranked.gmv,
    round(ranked.avg_review_score, 2)       as avg_review_score,
    round(ranked.late_delivery_rate, 4)     as late_delivery_rate,
    round(ranked.avg_delivery_days, 1)      as avg_delivery_days,
    ranked.first_sale_at,
    ranked.last_sale_at,
    ranked.gmv_rank,
    round(ranked.cumulative_gmv_share, 4)   as cumulative_gmv_share,
    case when ranked.cumulative_gmv_share <= 0.8 then 'head (80% of GMV)' else 'long tail' end as pareto_segment

from ranked
inner join sellers on ranked.seller_key = sellers.seller_key
