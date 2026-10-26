{#
    Text normalization used by entity resolution. The same race shows up as
    "15ª Corrida APAE Run - 2026", "APAE RUN 2026 - Pix" and "Corrida APAE Run":
    lower case, no accents, no edition numbers/years/ordinals, no generic words, no payment suffixes.
#}
{% macro normalize_name(column) -%}
    trim(regexp_replace(
        regexp_replace(
            regexp_replace(
                regexp_replace(lower(strip_accents({{ column }})),
                    '\s*-\s*(pix|cartao|boleto|pcd|60\+|kids)\s*$', '', 'g'),  -- payment/category variants
                '\b\d+\s*(a|o|ª|º)?\s*(edicao)?\b|\b(19|20)\d{2}\b', ' ', 'g'),  -- ordinals, editions, years
            '\b(corrida|run|rustica|de|da|do|das|dos|e|the|edicao|etapa|oficial)\b|[^a-z0-9 ]', ' ', 'g'),
        '\s+', ' ', 'g'))
{%- endmacro %}

{% macro normalize_city(column) -%}
    trim(regexp_replace(lower(strip_accents({{ column }})), '[^a-z0-9 ]', ' ', 'g'))
{%- endmacro %}

{#- Distance in km -> the categories the app filters by. -#}
{% macro distance_category(km) -%}
    case
        when {{ km }} between 4.5 and 5.5 then '5k'
        when {{ km }} between 9.5 and 10.5 then '10k'
        when {{ km }} between 20.9 and 21.3 then '21k'
        when {{ km }} between 42.0 and 42.4 then '42k'
        else 'other'
    end
{%- endmacro %}
