-- Current-state customer dimension (SCD type 1: overwritten on every build).
-- Exercise 5 builds the SCD type 2 version on top of the snapshot.
with customers as (

    select * from {{ ref('stg_bookstore__customers') }}

),

countries as (

    select * from {{ ref('country_codes') }}

)

select
    customers.customer_id,
    customers.full_name,
    customers.email,
    customers.country_code,
    countries.country_name,
    countries.region,
    customers.tier,
    customers.created_at,
    customers.updated_at

from customers
left join countries
    on customers.country_code = countries.country_code
