select
    sender_account_id,
    count(*) as total_txns_sent,
    sum(amount) as total_amount_sent,
    avg(amount) as avg_amount_sent,
    approx_percentile(amount, .5) as median_amount_sent,
    stddev(amount) as stddev_amount_sent,
    count(distinct receiver_account_id) as distinct_receivers_count,
    min(transaction_date) as first_txn_date,
    max(transaction_date) as last_txn_date,
    date_diff('day', min(transaction_date), max(transaction_date)) as days_active
from {{ref('stg_transactions')}}
where is_fraud = false
group by sender_account_id