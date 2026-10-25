{#
    Use custom schema names as-is (staging, core, analytics...) instead of dbt's default
    <target_schema>_<custom_schema>. Single developer, single target: no collisions to avoid.
    In a team setup you would keep the default for dev targets and use this only in prod.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
