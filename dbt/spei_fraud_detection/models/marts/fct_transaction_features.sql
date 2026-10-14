with
    transactions as (
        select
            transaction_id,
            sender_account_id,
            receiver_account_id,
            transaction_date,
            amount,
            concept_pago,
            is_fraud
        from {{ ref('stg_transactions') }}
    ),

    sender_lifetime as (
        select
            sender_account_id,
            avg_amount_sent,
            median_amount_sent
        from {{ ref('int_sender_lifetime_stats') }}
    ),

    sender_rolling as (
        select
            transaction_id,
            sender_txn_count_24h,
            sender_txn_count_7d,
            sender_txn_count_30d,
            sender_amount_sum_24h,
            sender_amount_avg_24h,
            sender_amount_max_7d,
            sender_distinct_receivers_as_of,
            pair_txn_count_as_of
        from {{ ref('int_sender_rolling_stats') }}
    ),

    receiver_lifetime as (
        select
            receiver_account_id,
            total_txns_received
        from {{ ref('int_receiver_lifetime_stats') }}
    ),

    receiver_rolling as (
        select
            transaction_id,
            receiver_txn_count_24h,
            receiver_txn_count_7d,
            receiver_txn_count_30d,
            receiver_amount_max_7d,
            receiver_distinct_senders_as_of
        from {{ ref('int_receiver_rolling_stats') }}
    ),

    accounts as (
        select
            account_id,
            kyc_tier,
            activity_segment
        from {{ ref('stg_accounts') }}
    )

select
    -- Base passthrough fields
    t.transaction_id,
    t.sender_account_id,
    t.receiver_account_id,
    t.transaction_date,
    t.amount,
    t.concept_pago,

    -- Temporal features
    hour(t.transaction_date) as hour,
    day_of_week(t.transaction_date) as day_of_week,
    case
        when hour(t.transaction_date) between 0 and 5
          or hour(t.transaction_date) between 22 and 23
        then true
        else false
    end as is_off_hours,

    -- Amount features
    t.amount / nullif(sl.avg_amount_sent, 0) as amount_vs_sender_avg,
    t.amount / nullif(sl.median_amount_sent, 0) as amount_vs_sender_median,
    case
        when t.amount between 11000 and 13200
        then true
        else false
    end as near_threshold_flag,

    -- Sender behavior features
    sr.sender_txn_count_24h,
    sr.sender_txn_count_7d,
    sr.sender_txn_count_30d,
    sr.sender_amount_sum_24h,
    sr.sender_amount_avg_24h,
    sr.sender_amount_max_7d,
    sr.sender_distinct_receivers_as_of,

    -- Sender behavioral change ratio
    sr.sender_txn_count_24h / nullif(sr.sender_txn_count_30d / 30.0, 0)
        as sender_txn_count_vs_30d_avg,

    -- Receiver behavior features
    rr.receiver_txn_count_24h,
    rr.receiver_txn_count_7d,
    rr.receiver_txn_count_30d,
    rr.receiver_amount_max_7d,
    rr.receiver_distinct_senders_as_of,
    rl.total_txns_received,

    -- Receiver behavioral change ratio
    rr.receiver_txn_count_24h / nullif(rr.receiver_txn_count_30d / 30.0, 0)
        as receiver_txn_count_vs_30d_avg,

    -- Beneficiary features (now from int_sender_rolling_stats)
    case when sr.pair_txn_count_as_of = 0 then true else false end as is_new_beneficiary,
    sr.pair_txn_count_as_of as pair_txn_count,

    -- Account context features
    a.kyc_tier as sender_kyc_tier,
    a.activity_segment as sender_activity_segment,

    -- Target
    t.is_fraud

from transactions t
left join sender_lifetime sl
    on t.sender_account_id = sl.sender_account_id
left join sender_rolling sr
    on t.transaction_id = sr.transaction_id
left join receiver_lifetime rl
    on t.receiver_account_id = rl.receiver_account_id
left join receiver_rolling rr
    on t.transaction_id = rr.transaction_id
left join accounts a
    on t.sender_account_id = a.account_id