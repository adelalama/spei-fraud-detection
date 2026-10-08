{% macro running_distinct_count(partition_column, prefix, counterparty_label) %}
    sum(case when is_fraud = false then is_first_pair_occurrence end) over(
        partition by {{ partition_column }}
        order by transaction_date
        rows between unbounded preceding and 1 preceding
    ) as {{prefix}}_distinct_{{counterparty_label}}_as_of
{% endmacro %}