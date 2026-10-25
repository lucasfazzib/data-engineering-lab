{{ config(enabled=false) }}  -- EXERCISE 2: remove this line once the model is done

-- Intermediate = reusable building block between staging and marts.
-- Materialized as EPHEMERAL (see dbt_project.yml): it never exists in the database,
-- dbt inlines it as a CTE into whatever model refs it. Check target/compiled/ to see that.

-- TODO (exercise 2): join stg_bookstore__order_items with stg_bookstore__books
--   output grain: one row per order item, with book title/category and line_amount_cents.

select 1 as todo
