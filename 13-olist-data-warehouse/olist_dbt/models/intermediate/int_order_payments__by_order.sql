-- Payments rolled up to order grain. An order can be paid with several methods (e.g. voucher + credit card).
with payments as (

    select * from {{ ref('stg_olist__order_payments') }}

)

select
    order_id,
    count(*)                                            as payment_count,
    sum(payment_value)                                  as payment_value,
    max(installments)                                   as max_installments,
    -- the method that paid the largest share of the order
    arg_max(payment_type, payment_value)                as primary_payment_type,
    bool_or(payment_type = 'voucher')                   as used_voucher

from payments
group by order_id
