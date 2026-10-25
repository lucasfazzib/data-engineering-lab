-- An order cannot be delivered before it was purchased.
select
    order_id,
    purchased_at,
    delivered_to_customer_at
from {{ ref('fct_orders') }}
where delivered_to_customer_at < purchased_at
