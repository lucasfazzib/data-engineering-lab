select
    source,
    started_at,
    finished_at,
    records,
    errors
from {{ source('bronze', 'runs') }}
