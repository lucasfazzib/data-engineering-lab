{% macro cents_to_currency(column_name, scale=2) -%}
    round(cast({{ column_name }} as decimal(18, 4)) / 100, {{ scale }})
{%- endmacro %}
