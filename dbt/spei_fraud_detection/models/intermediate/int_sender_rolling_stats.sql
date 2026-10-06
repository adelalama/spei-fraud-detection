select
    transaction_id,
    sender_account_id,
    transaction_date,
    amount,

    count(*) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '24' hour preceding and interval '1' second preceding
    ) as sender_txn_count_24h,

    sum(amount) over (
        partition by sender_account_id
        order by transaction_date
        range between interval '24' hour preceding and interval '1' second preceding
    ) as sender_amount_sum_24h,

    avg(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '24' hour preceding and interval '1' second preceding
    ) as sender_amount_avg_24h,

    max(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '24' hour preceding and interval '1' second preceding
    ) as sender_amount_max_24h,


    count(*) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '7' day preceding and interval '1' second preceding
    ) as sender_txn_count_7d,

    sum(amount) over (
        partition by sender_account_id
        order by transaction_date
        range between interval '7' day preceding and interval '1' second preceding
    ) as sender_amount_sum_7d,

    avg(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '7' day preceding and interval '1' second preceding
    ) as sender_amount_avg_7d,

    max(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '7' day preceding and interval '1' second preceding
    ) as sender_amount_max_7d,


    count(*) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '30' day preceding and interval '1' second preceding
    ) as sender_txn_count_30d,

    sum(amount) over (
        partition by sender_account_id
        order by transaction_date
        range between interval '30' day preceding and interval '1' second preceding
    ) as sender_amount_sum_30d,

    avg(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '30' day preceding and interval '1' second preceding
    ) as sender_amount_avg_30d,

    max(amount) over(
        partition by sender_account_id
        order by transaction_date
        range between interval '30' day preceding and interval '1' second preceding
    ) as sender_amount_max_30d

from {{ref('stg_transactions')}}
where is_fraud = false