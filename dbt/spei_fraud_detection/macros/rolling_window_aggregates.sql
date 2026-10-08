{% macro rolling_window_aggregates(partition_column, prefix) %}

    {% set windows = [
        ('24h', '24', 'hour'),
        ('7d', '7', 'day'),
        ('30d', '30', 'day'),
    ] %}
    {% set aggregates = [
        ('count', '*', 'txn_count'),
        ('sum', 'amount', 'amount_sum'),
        ('avg', 'amount', 'amount_avg'),
        ('max', 'amount', 'amount_max'),
    ] %}

    {% set ns = namespace(count=0) %}
    {% set total = windows|length * aggregates|length %}

    {% for window_label, window_value, window_unit in windows %}
        {% for agg_func, agg_column, agg_alias in aggregates %}
            {% set ns.count = ns.count + 1 %}
            {{ agg_func }}({{ agg_column }}) over (
                partition by {{ partition_column }}
                order by transaction_date
                range between interval '{{ window_value }}' {{ window_unit }} preceding and interval '1' second preceding
            ) as {{ prefix }}_{{ agg_alias }}_{{ window_label }}{% if ns.count < total %},{% endif %}
        {% endfor %}
    {% endfor %}

{% endmacro %}