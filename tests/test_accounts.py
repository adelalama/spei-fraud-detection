import pandas as pd
import pytest
from src.data_generator.accounts import generate_accounts
from src.data_generator.clabe import validate_clabe
from src.data_generator.config import DEFAULT_N_ACCOUNTS, DEFAULT_SEED, SIMULATION_START, SIMULATION_END
from datetime import timedelta
from src.data_generator.institutions import institutions

df = generate_accounts(DEFAULT_N_ACCOUNTS)

def test_generation_is_reproducible():
    df1 = generate_accounts(1000, seed=DEFAULT_SEED)
    df2 = generate_accounts(1000, seed =DEFAULT_SEED)
    assert df1.equals(df2)

def test_clabe_unique():
    assert df['clabe'].nunique() == len(df)

def test_account_id_unique():
    assert df['account_id'].nunique() == len(df)

def test_kyc_in_range():
    assert df['kyc_tier'].isin([1, 2, 3, 4]).all()

def test_creation_dates_within_expected_range():
    earliest_allowed = SIMULATION_START - timedelta(days=1825)
    latest_allowed = SIMULATION_END
    assert (df['creation_date'] >= pd.Timestamp(earliest_allowed)).all()
    assert (df['creation_date'] <= pd.Timestamp(latest_allowed)).all()

def test_phone_length():
    assert (df['phone_number'].str.len() == 10).all()

def test_phone_unique_per_person():
    phones_per_person = df.groupby('person_id')['phone_number'].nunique()
    assert (phones_per_person == 1).all()

def test_generated_clabes_are_valid():
    assert df['clabe'].apply(validate_clabe).all()

def test_bank_distribution_weights():
    actual = df['bank_code'].value_counts(normalize=True)
    expected = institutions.set_index('bank_code')['weight'] / institutions['weight'].sum()

    for bank_code in expected.nlargest(5).index:
        assert abs(actual[bank_code] - expected[bank_code]) < 0.01

def test_kyc_distribution_per_institution_type():
    merged = df.merge(institutions, on ='bank_code')
    actual = merged.groupby('institution_type')['kyc_tier'].value_counts(normalize=True)

    assert abs(actual[('banco_multiple', 3)] - .4) < .03
    assert abs(actual[('casa_bolsa', 4)] - .8) < .03

def test_activity_segment_dist():
    actual = df['activity_segment'].value_counts(normalize=True)

    expected = {
    'dormant' : .15,
    'light' : .50,
    'regular': .25,
    'heavy': .08,
    'power': .02
}
    for segment, expected_pct in expected.items():
        assert abs(actual[segment] - expected_pct) < 0.01






