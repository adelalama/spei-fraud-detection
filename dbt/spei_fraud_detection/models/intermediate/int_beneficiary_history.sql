select
    sender_account_id,
    receiver_account_id,
    count(*) as pair_txn_count,
    sum(amount) as pair_total_amount,
    avg(amount) as pair_avg_amount,
    min(transaction_date) as pair_first_txn_date,
    max(transaction_date) as pair_last_txn_date,
    date_diff('day', min(transaction_date), max(transaction_date)) as pair_days_span
from {{ref('stg_transactions')}}
where is_fraud = false
group by sender_account_id, receiver_account_id
