{{ config(enabled=false) }}  -- EXERCISE 2: remove this line once the model is done

{#
    TODO (exercise 2): one row per order with
        order_id, customer_id, status, ordered_at, updated_at,
        item_count, total_quantity, order_amount_cents, order_amount (use cents_to_currency)
    Source: stg_bookstore__orders + int_order_items_enriched, aggregated to order grain BEFORE
    joining — why? Write the answer in NOTES.md.

    TODO (exercise 4): turn this model into an INCREMENTAL model:
        {{ config(materialized='incremental', unique_key='order_id', incremental_strategy=...) }}
    and filter only new/changed rows inside
        {% if is_incremental() %} ... {% endif %}
#}

select 1 as todo
