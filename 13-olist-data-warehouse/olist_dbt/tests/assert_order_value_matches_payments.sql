-- Paid amount should match items + freight. Known exceptions: installment interest and vouchers.
-- Severity warn: the mismatches are a property of the source, documented in the README, not a pipeline bug.
{{ config(severity='warn') }}

select
    order_id,
    order_value,
    payment_value,
    payment_value - order_value as difference
from {{ ref('fct_orders') }}
where
    is_sale
    and payment_count > 0
    and abs(payment_value - order_value) > 1.00
