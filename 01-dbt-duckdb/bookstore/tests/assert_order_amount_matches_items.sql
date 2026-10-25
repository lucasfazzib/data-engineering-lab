{{ config(enabled=false) }}  -- EXERCISE 3: remove this line once fct_orders exists

-- Singular test: a plain SELECT that returns the rows that violate a business rule.
-- TODO (exercise 3): return orders where fct_orders.order_amount_cents differs from the sum of
--   quantity * unit_price_cents in stg_bookstore__order_items for that order.

select 1 as todo
where false
