-- Entity resolution, step 2: matched pairs -> clusters (connected components).
-- If A~B and B~C, all three are one event even if A and C were never compared directly.
-- Label propagation with a recursive CTE: every record starts with its own key as label and
-- repeatedly takes the smallest label among its neighbours until nothing changes.
with recursive edges as (
    select left_key as a, right_key as b from {{ ref('int_er__candidate_pairs') }} where decision = 'match'
    union all
    select right_key, left_key from {{ ref('int_er__candidate_pairs') }} where decision = 'match'
),

labels(record_key, label, depth) as (
    select record_key, record_key, 0 from {{ ref('int_events__normalized') }}
    union all
    select e.b, l.label, l.depth + 1
    from labels as l
    inner join edges as e on l.record_key = e.a
    where l.depth < 10  -- clusters are tiny; the bound guarantees termination
)

select
    record_key,
    min(label) as cluster_key,
    'evt_' || left(md5(min(label)), 12) as event_id  -- stable while the cluster's smallest member stays
from labels
group by record_key
