select
    transaction_id,
    sender_account_id,
    transaction_date,
    amount,

    {{ rolling_window_aggregates('sender_account_id', 'sender') }}

from {{ref('stg_transactions')}}
where is_fraud = false