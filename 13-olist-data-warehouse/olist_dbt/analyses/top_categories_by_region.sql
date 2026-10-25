-- Analyses are compiled (dbt compile) but never materialized: version-controlled ad-hoc SQL.
-- Top 3 categories by GMV in each customer region.
with items as (

    select * from {{ ref('fct_order_items') }}
    where is_sale

),

ranked as (

    select
        customers.region,
        products.category_name_en,
        sum(items.price) as gmv,
        row_number() over (partition by customers.region order by sum(items.price) desc) as rank_in_region
    from items
    inner join {{ ref('dim_products') }} as products on items.product_key = products.product_key
    inner join {{ ref('dim_customers') }} as customers on items.customer_key = customers.customer_key
    group by customers.region, products.category_name_en

)

select * from ranked
where rank_in_region <= 3
order by region, rank_in_region
