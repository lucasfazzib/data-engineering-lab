-- Delivery performance by destination state — and how lateness hurts review scores.
with delivered as (

    select * from {{ ref('fct_orders') }}
    where is_delivered

),

states as (

    select * from {{ ref('br_states') }}

)

select
    delivered.delivery_state_code                                           as state_code,
    states.state_name,
    states.region,
    count(*)                                                                as delivered_orders,
    round(avg(delivered.delivery_days), 1)                                  as avg_delivery_days,
    round(avg(delivered.estimated_delivery_days), 1)                        as avg_estimated_days,
    round(avg(case when delivered.is_late then 1.0 else 0.0 end), 4)        as late_delivery_rate,
    round(avg(delivered.review_score) filter (where not delivered.is_late), 2) as avg_review_on_time,
    round(avg(delivered.review_score) filter (where delivered.is_late), 2)     as avg_review_late,
    round(avg(delivered.freight_value / nullif(delivered.order_value, 0)), 4)  as avg_freight_share

from delivered
left join states on delivered.delivery_state_code = states.state_code
group by 1, 2, 3
