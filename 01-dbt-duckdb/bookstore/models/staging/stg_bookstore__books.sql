{{ config(enabled=false) }}  -- EXERCISE 1: remove this line once the model is done

-- TODO (exercise 1): staging model for source('bookstore', 'books').
--   - cast book_id to integer
--   - keep price in cents as integer (price_cents) AND add price using the cents_to_currency macro
--   - normalize category (lowercase, trimmed)
--   - follow the same CTE layout as stg_bookstore__customers.sql (source -> renamed -> final select)

select 1 as todo
