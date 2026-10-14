with transactions_with_flags as (
    select
        transaction_id,
        sender_account_id,
        receiver_account_id,
        transaction_date,
        amount,
        is_fraud,
        case when row_number() over(
            partition by sender_account_id, receiver_account_id
            order by transaction_date
        ) = 1 then 1 else 0 end as is_first_pair_occurrence
    from {{ ref('stg_transactions') }}
)

select
    transaction_id,
    sender_account_id,
    receiver_account_id,
    transaction_date,
    amount,
    is_fraud,

    {{ rolling_window_aggregates('sender_account_id', 'sender') }},

    {{ running_distinct_count('sender_account_id', 'sender', 'receivers')}},

    count(case when is_fraud = false then 1 end) over (
        partition by sender_account_id, receiver_account_id
        order by transaction_date
        rows between unbounded preceding and 1 preceding
    ) as pair_txn_count_as_of

from transactions_with_flags