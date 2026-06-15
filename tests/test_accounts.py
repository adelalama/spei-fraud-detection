import pandas as pd
import pytest
from src.data_generator.accounts import generate_accounts
from src.data_generator.config import DEFAULT_N_ACCOUNTS, DEFAULT_SEED, SIMULATION_START, SIMULATION_END
from datetime import timedelta

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



