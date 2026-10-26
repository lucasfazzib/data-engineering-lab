-- Ambiguous pairs (score between er_review_min and er_auto_match): a human should look at these.
select
    left_key,
    right_key,
    left_name,
    right_name,
    left_date,
    right_date,
    municipality,
    round(name_similarity, 3) as name_similarity,
    round(distance_overlap, 3) as distance_overlap,
    score
from {{ ref('int_er__candidate_pairs') }}
where decision = 'review'
