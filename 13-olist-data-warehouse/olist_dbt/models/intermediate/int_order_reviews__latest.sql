-- Some orders have several reviews and some review_ids repeat across orders.
-- Rule: one review per order — the most recently answered one (ties broken deterministically).
with reviews as (

    select * from {{ ref('stg_olist__order_reviews') }}

)

select
    order_id,
    review_id,
    review_score,
    comment_title,
    comment_message,
    created_at,
    answered_at

from reviews
qualify row_number() over (
    partition by order_id
    order by answered_at desc, created_at desc, review_id asc
) = 1
