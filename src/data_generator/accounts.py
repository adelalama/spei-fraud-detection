import pandas as pd
import numpy as np
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

def generate_accounts(n:int = 60_000, seed: int = 42) -> pd.DataFrame:

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

    data = {
        "account_id" : account_ids,
        "person_id" : expanded_persons_id,
        "bank_code" : sampled_bank_codes,
        "plaza_code" : sampled_plazas,
        "account_number" : account_number_str,
        "clabe" : clabes,
        "kyc_tier" : kyc_tiers,
    }
    return pd.DataFrame(data)



if __name__ == "__main__":
    df = generate_accounts(60_000)
    print(df.head(20))
    print(f"Total accounts: {len(df)}")
    print(f"Total persons: {df['person_id'].nunique()}")
    print(f"Accounts per person distribution:")
    print(df.groupby('person_id').size().value_counts().sort_index())
    print(df['bank_code'].value_counts(normalize=True).head(10))
    print(df['plaza_code'].value_counts(normalize=True))
    print(f"Unique CLABEs: {df['clabe'].nunique()} / {len(df)}")
    assert all(len(c) == 18 for c in df['clabe']), "Some CLABEs not 18 chars"
    print(df.merge(institutions, on='bank_code').groupby('institution_type')['kyc_tier'].value_counts(
        normalize=True).sort_index())
    assert df['kyc_tier'].isin([1,2,3,4]).all(), "Some tiers are not valid"