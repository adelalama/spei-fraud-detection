select
    transaction_id,
    sender_account_id,
    sender_clabe,
    receiver_account_id,
    receiver_clabe,
    amount,
    transaction_date,
    concept_pago,
    status,
    is_fraud,
    fraud_typology,
    fraud_event_id
from {{ source('spei_raw', 'transactions') }}