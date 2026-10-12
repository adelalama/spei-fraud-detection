with
    accounts as (
        select
            account_id,
            clabe,
            kyc_tier,
            activity_segment,
            creation_date
        from {{ ref('stg_accounts') }}
    ),

    sender_stats as (
        select
            sender_account_id,
            total_txns_sent,
            total_amount_sent,
            avg_amount_sent,
            distinct_receivers_count
        from {{ ref('int_sender_lifetime_stats') }}
    ),

    receiver_stats as (
        select
            receiver_account_id,
            total_txns_received,
            total_amount_received,
            distinct_senders_count
        from {{ ref('int_receiver_lifetime_stats') }}
    ),

    fraud_as_sender as (
        select
            sender_account_id,
            count(*) as fraud_txns_sent
        from {{ ref('stg_transactions') }}
        where is_fraud = true
        group by sender_account_id
    ),

    fraud_as_receiver as (
        select
            receiver_account_id,
            count(*) as fraud_txns_received
        from {{ ref('stg_transactions') }}
        where is_fraud = true
        group by receiver_account_id
    )

select
    a.account_id,
    a.clabe,
    a.kyc_tier,
    a.activity_segment,
    a.creation_date,

    coalesce(ss.total_txns_sent, 0) as total_txns_sent,
    ss.total_amount_sent,
    ss.avg_amount_sent,
    coalesce(ss.distinct_receivers_count, 0) as distinct_receivers_count,

    coalesce(rs.total_txns_received, 0) as total_txns_received,
    rs.total_amount_received,
    coalesce(rs.distinct_senders_count, 0) as distinct_senders_count,

    coalesce(fs.fraud_txns_sent, 0) as fraud_txns_sent,
    coalesce(fr.fraud_txns_received, 0) as fraud_txns_received,

    cast(coalesce(fs.fraud_txns_sent, 0) as double)
    / nullif(coalesce(ss.total_txns_sent, 0) + coalesce(fs.fraud_txns_sent,0), 0)
    as fraud_rate_as_sender,
    cast(coalesce(fr.fraud_txns_received, 0) as double)
    / nullif(coalesce(rs.total_txns_received, 0) + coalesce(fr.fraud_txns_received, 0), 0)
    as fraud_rate_as_receiver

from accounts a
left join sender_stats ss on a.account_id = ss.sender_account_id
left join receiver_stats rs on a.account_id = rs.receiver_account_id
left join fraud_as_sender fs on a.account_id = fs.sender_account_id
left join fraud_as_receiver fr on a.account_id = fr.receiver_account_id