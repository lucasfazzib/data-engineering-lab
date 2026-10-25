{#
    By default dbt builds custom schemas as <target_schema>_<custom_schema> (e.g. main_staging),
    so several developers can share one warehouse without colliding.
    This lab has a single user, so we use the custom schema name as-is: staging, marts, seeds.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
