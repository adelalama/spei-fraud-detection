select
    receiver_account_id,
    count(*) as total_txns_received,
    sum(amount) as total_amount_received,
    avg(amount) as avg_amount_received,
    approx_percentile(amount, .5) as median_amount_received,
    stddev(amount) as stddev_amount_received,
    count(distinct sender_account_id) as distinct_senders_count,
    min(transaction_date) as first_received_date,
    max(transaction_date) as last_received_date,
    date_diff('day', min(transaction_date), max(transaction_date)) as days_active_as_receiver
from {{ref('stg_transactions')}}
where is_fraud = false
group by receiver_account_id