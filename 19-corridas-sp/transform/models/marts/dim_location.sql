select
    ibge_code,
    municipality,
    uf,
    lat,
    lon
from {{ ref('stg_reference__municipalities') }}
