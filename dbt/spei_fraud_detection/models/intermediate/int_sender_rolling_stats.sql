select
    transaction_id,
    sender_account_id,
    transaction_date,
    amount,
    is_fraud,

    {{ rolling_window_aggregates('sender_account_id', 'sender') }}

from {{ref('stg_transactions')}}