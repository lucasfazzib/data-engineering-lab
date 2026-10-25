-- Monthly sales KPIs. The first and last months of the dataset are partial: use `in_analysis_window`.
with sales as (

    select * from {{ ref('fct_orders') }}
    where is_sale

),

monthly as (

    select
        cast(date_trunc('month', purchased_at) as date)     as month,
        count(*)                                            as orders,
        count(distinct customer_key)                        as customers,
        sum(items_value)                                    as gmv,
        sum(freight_value)                                  as freight,
        avg(review_score)                                   as avg_review_score,
        avg(case when is_late then 1.0 when not is_late then 0.0 end) as late_delivery_rate
    from sales
    group by 1

)

select
    month,
    month between cast('{{ var("analysis_start_month") }}' as date)
    and cast('{{ var("analysis_end_month") }}' as date)  as in_analysis_window,
    orders,
    customers,
    gmv,
    round(gmv / orders, 2)                                          as avg_order_value,
    freight,
    round(freight / (gmv + freight), 4)                             as freight_share,
    round(avg_review_score, 2)                                      as avg_review_score,
    round(late_delivery_rate, 4)                                    as late_delivery_rate,
    round(gmv / lag(gmv) over (order by month) - 1, 4)              as gmv_mom_growth,
    sum(gmv) over (order by month rows between unbounded preceding and current row) as cumulative_gmv

from monthly
