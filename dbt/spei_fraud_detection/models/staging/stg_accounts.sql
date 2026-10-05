select
    account_id,
    person_id,
    bank_code,
    plaza_code,
    account_number,
    clabe,
    kyc_tier,
    creation_date,
    phone_number,
    activity_segment,
    mule_type
from {{ source('spei_raw', 'accounts')}}