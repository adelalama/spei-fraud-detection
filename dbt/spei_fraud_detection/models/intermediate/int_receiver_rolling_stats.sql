select
    transaction_id,
    sender_account_id,
    receiver_account_id,
    transaction_date,
    amount,
    is_fraud,

    {{ rolling_window_aggregates('receiver_account_id', 'receiver') }}

from {{ref('stg_transactions')}}
