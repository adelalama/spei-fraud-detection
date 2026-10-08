with transactions_with_flags as (
    select
        transaction_id,
        sender_account_id,
        receiver_account_id,
        transaction_date,
        amount,
        is_fraud,
        case when row_number() over (
            partition by receiver_account_id, sender_account_id
            order by transaction_date
        ) = 1 then 1 else 0 end as is_first_pair_occurrence
    from {{ref('stg_transactions')}}
)

select
    transaction_id,
    sender_account_id,
    receiver_account_id,
    transaction_date,
    amount,
    is_fraud,

    {{ rolling_window_aggregates('receiver_account_id', 'receiver') }},

    {{ running_distinct_count('receiver_account_id', 'receiver', 'senders')}}

from transactions_with_flags
