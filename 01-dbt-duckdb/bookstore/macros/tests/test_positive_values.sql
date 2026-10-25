{#
    EXERCISE 3 — custom generic test.

    A generic test is a macro named `test_<name>` that returns a query selecting the FAILING rows.
    Zero rows returned = test passes. Once implemented, use it in YAML like:

        columns:
          - name: quantity
            data_tests:
              - positive_values

    TODO: return the rows where {{ column_name }} is not strictly positive.
          Decide (and justify in NOTES.md) whether NULLs should fail this test or not.
#}
{% test positive_values(model, column_name) %}

    select *
    from {{ model }}
    where false  -- TODO: replace with the real condition

{% endtest %}
