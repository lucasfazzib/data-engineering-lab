-- Monthly acquisition cohorts: of the customers who first bought in month M, how many bought again N months later?
with sales as (

    select
        customer_key,
        cast(date_trunc('month', purchased_at) as date) as order_month
    from {{ ref('fct_orders') }}
    where is_sale

),

first_purchase as (

    select
        customer_key,
        min(order_month) as cohort_month
    from sales
    group by 1

),

activity as (

    select distinct
        first_purchase.cohort_month,
        date_diff('month', first_purchase.cohort_month, sales.order_month) as months_since_first_order,
        sales.customer_key
    from sales
    inner join first_purchase on sales.customer_key = first_purchase.customer_key

),

cohort_counts as (

    select
        cohort_month,
        months_since_first_order,
        count(*) as active_customers
    from activity
    group by 1, 2

)

select
    cohort_month,
    months_since_first_order,
    active_customers,
    max(active_customers) filter (where months_since_first_order = 0)
        over (partition by cohort_month)                                    as cohort_size,
    round(active_customers / max(active_customers) filter (where months_since_first_order = 0)
        over (partition by cohort_month), 4)                                as retention_rate

from cohort_counts
