select
    ibge_code,
    name as municipality,
    uf,
    {{ normalize_city('name') }} as city_key,
    lat,
    lon
from {{ source('reference', 'municipalities') }}
