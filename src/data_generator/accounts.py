from datetime import timedelta

import pandas as pd
import numpy as np
from src.data_generator.config import DEFAULT_SEED, DEFAULT_N_ACCOUNTS, SIMULATION_START, SIMULATION_END
from src.data_generator.institutions import institutions
from src.data_generator.clabe import generate_clabe, validate_clabe

PLAZA_WEIGHTS = {
    '180': 60, #cdmx
    '127': 12, #guadalajara
    '031': 10, #monterrey
    '001': 4, #aguascalientes
    '067': 4, #leon
    '071': 3, #merida
    '010': 3, #cuernavaca
    '021': 4 #puebla
}

KYC_DISTRIBUTIONS = {
    'banco_multiple' : [.0, 0.3, 0.4, 0.3],
    'ifpe' : [.05, .5, .35, .1],
    'sofipo' : [.15, .5, .3 ,.05],
    'casa_bolsa' : [.0, .0, .2, .8]
}

MOBILE_AREA_CODES = ['55', '33', '81', '449', '477', '999', '777', '222']
AREA_CODE_WEIGHTS = [60, 12, 10, 4, 4, 3, 3, 4]


def generate_accounts(n: int = DEFAULT_N_ACCOUNTS, seed: int = DEFAULT_SEED) -> pd.DataFrame:

    rng = np.random.default_rng(seed)

    # Building account_id and person_id columns
    tail_values = np.arange(3, 16)
    tail_weights = np.array ([100, 70, 50, 35, 25, 18, 12, 8, 5, 3, 2, 1.5, 1])
    tail_odds = tail_weights / tail_weights.sum()
    tail_mean = (tail_values * tail_odds).sum()
    expected_per_person = (.6 * 1) + (.25 * 2) + (.15 * tail_mean)
    n_persons = int(n / expected_per_person)

    b1 =  int(n_persons * .6)
    b2 = int(n_persons * .25)
    n_tail = int(n_persons * .15)

    counts_1 = np.ones(b1, dtype=int)
    counts_2 = np.full(b2, 2, dtype=int)
    counts_tail = rng.choice(tail_values, size=n_tail, p=tail_odds)

    all_counts = np.concatenate([counts_1, counts_2, counts_tail])
    total_persons = len(all_counts)
    persons_id = np.arange(total_persons)
    expanded_persons_id = np.repeat(persons_id, all_counts)
    account_ids = np.arange(len(expanded_persons_id))

    n_accounts = len(account_ids)

    #bank_codes column
    bank_codes_pool = institutions['bank_code'].values
    bank_odds = institutions['weight'].values / institutions['weight'].sum()
    sampled_bank_codes = rng.choice(bank_codes_pool, size = n_accounts, p = bank_odds)

    #plaza codes column
    plaza_codes_pool = np.array(list(PLAZA_WEIGHTS.keys()))
    plaza_weights = np.array(list(PLAZA_WEIGHTS.values()))
    plaza_probs = plaza_weights / plaza_weights.sum()
    sampled_plazas = rng.choice(plaza_codes_pool, size = n_accounts, p = plaza_probs)

    #account # column
    account_number = rng.integers(0, 10**11, size = n_accounts)
    account_number_str = [str(n).zfill(11) for n in account_number]

    #clabes column
    clabes = [generate_clabe(b, p, a) for b, p, a in zip(sampled_bank_codes, sampled_plazas, account_number_str)]

    #kyc column
    account_inst_type = institutions[['bank_code', 'institution_type']].set_index('bank_code')
    inst_type_per_account = account_inst_type.loc[sampled_bank_codes, 'institution_type'].values

    kyc_tiers = np.zeros(n_accounts, dtype=int)
    for inst_type, probs in KYC_DISTRIBUTIONS.items():
        mask = inst_type_per_account == inst_type
        n_in_group = mask.sum()
        if n_in_group > 0:
            kyc_tiers[mask] = rng.choice([1, 2, 3, 4], size = n_in_group, p = probs)

    #time creation boundries generated from simulation_start

    in_window_start = SIMULATION_START
    in_window_end = SIMULATION_END
    recent_start = SIMULATION_START - timedelta(days = 730)
    recent_end = SIMULATION_START
    mid_start = SIMULATION_START - timedelta(days = 1460)
    mid_end = SIMULATION_START -  timedelta(days = 730)
    old_start = SIMULATION_START - timedelta(days = 1825)
    old_end = SIMULATION_START - timedelta(days = 1460)

    date_ranges = {
        'in_window' : (in_window_start, in_window_end),
        'recent' : (recent_start, recent_end),
        'mid' : (mid_start, mid_end),
        'older_start' : (old_start, old_end),
    }
    bucket_names = ['in_window', 'recent', 'mid', 'older_start']
    bucket_weights = [.3, .4, .2, .1]
    assigned_buckets = rng.choice(bucket_names, size = n_accounts, p = bucket_weights)
    creation_dates = np.full(n_accounts, np.datetime64('NaT') , dtype='datetime64[D]')
    for bucket_name, (start, end) in date_ranges.items():
        mask = assigned_buckets == bucket_name
        n_in_bucket = mask.sum()
        if n_in_bucket > 0:
            days_in_range = (end-start).days
            days_offset = rng.integers(0, days_in_range, size = n_in_bucket)
            dates = pd.Timestamp(start) + pd.to_timedelta(days_offset, 'D')
            creation_dates[mask] = dates

    #generating phone # for each person

    area_code_probs = np.array(AREA_CODE_WEIGHTS)/sum(AREA_CODE_WEIGHTS)
    sorted_area_codes = rng.choice(MOBILE_AREA_CODES, size = total_persons, p = area_code_probs)

    phone_per_person = []
    for area_code in sorted_area_codes:
        remaining_digits = 10 - len(area_code)
        phone = rng.integers(0, 10**remaining_digits)
        phone_str = str(phone).zfill(remaining_digits)
        phone_per_person.append(area_code + phone_str)

    phone_numbers = np.array(phone_per_person)[expanded_persons_id]

    #add empty mule column

    mule_types = np.array([None] * n_accounts, dtype = object)

    data = {
        "account_id" : account_ids,
        "person_id" : expanded_persons_id,
        "bank_code" : sampled_bank_codes,
        "plaza_code" : sampled_plazas,
        "account_number" : account_number_str,
        "clabe" : clabes,
        "kyc_tier" : kyc_tiers,
        "creation_date" : creation_dates,
        "phone_number" : phone_numbers,
        "mule_type" : mule_types
    }

    #validation

    df = pd.DataFrame(data)

    earliest_allowed = SIMULATION_START - timedelta(days=1825)
    latest_allowed = SIMULATION_END
    assert (creation_dates >= np.datetime64(earliest_allowed)).all(), "Some dates before earliest allowed"
    assert (creation_dates <= np.datetime64(latest_allowed)).all(), "Some dates after latest allowed"
    assert df['account_id'].is_unique, "Account IDs must be unique"
    assert df['clabe'].is_unique, "CLABEs must be unique"
    assert df['kyc_tier'].isin([1, 2, 3, 4]).all(), "KYC tier out of range"
    assert df['mule_type'].isna().all()
    assert all(len(c) == 18 for c in df['clabe']), "Some CLABEs not 18 chars"

    return pd.DataFrame(data)



if __name__ == "__main__":
    df = generate_accounts(60_000)
    print(f"Total accounts: {len(df)}")
    print(f"Total persons: {df['person_id'].nunique()}")
    print(df.dtypes)
    print(df.shape)
