{{ config(enabled=false) }}  -- EXERCISE 1: remove this line once the model is done

-- TODO (exercise 1): staging model for source('bookstore', 'order_items').
--   - cast all ids and quantity to integer
--   - add line_amount_cents = quantity * unit_price_cents
--   - DO NOT filter bad rows here yet — exercise 3 is about catching them with tests first

select 1 as todo
