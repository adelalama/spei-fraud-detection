import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import timedelta

from src.data_generator.accounts import generate_accounts
from src.data_generator.transactions import generate_transactions
from src.data_generator.fraud_injection import inject_fraud
from src.data_generator.config import DEFAULT_SEED, SIMULATION_START, SIMULATION_END

accounts_df = generate_accounts(10_000)
transactions_df = generate_transactions(accounts_df)
final_df = inject_fraud(transactions_df, accounts_df)


def test_generation_is_reproducible():
    test1 = inject_fraud(transactions_df, accounts_df, DEFAULT_SEED)
    test2 = inject_fraud(transactions_df, accounts_df, DEFAULT_SEED)
    assert test1.equals(test2)

def test_fraud_rate_matches_target():
    fraud_rate = final_df['is_fraud'].mean()
    assert 0.014 <= fraud_rate <= 0.016

def test_all_typologies_present():
    valid_typologies = {'app_fraud', 'ato', 'mule_to_mule', 'smurfing', 'business_impersonation'}
    fraud_rows = final_df[final_df['is_fraud']]
    assert fraud_rows['fraud_typology'].isin(valid_typologies).all(), 'Invalid typology in df'

def test_column_schema():
    assert list(transactions_df.columns) == list(final_df.columns), 'DataFrame columns mismatch'


def test_fraud_event_id_uniqueness_per_typology():
    event_typology_counts = final_df[final_df['is_fraud']].groupby('fraud_event_id')['fraud_typology'].nunique()
    assert (event_typology_counts == 1).all(), 'fraud_event_id spans multiple typologies'

def test_transaction_id_sequential():
    assert (final_df['transaction_id'] == np.arange(len(final_df))).all(), 'transaction_id non sequential'

def test_chronological_order():
    assert final_df['transaction_date'].is_monotonic_increasing, 'Not chronologically sorted'

def test_is_fraud_typology_alignment():
    assert final_df[final_df['is_fraud']]['fraud_typology'].notna().all()
    assert final_df[~final_df['is_fraud']]['fraud_typology'].isna().all()

def test_app_fraud_amounts_medium_retail_dominant():
    app_df = final_df[final_df['fraud_typology'] == 'app_fraud']
    amounts_float = np.array([float(a) for a in app_df['amount']])
    median = np.median(amounts_float)
    assert 5_000 <= median <= 13_200, f'APP fraud median outside medium_retail range'

def test_ato_off_hours_skew():
    ato_df = final_df[final_df['fraud_typology'] == 'ato']
    hours = pd.Series(ato_df['transaction_date']).dt.hour
    off_hours_share = ((hours >= 0) & (hours <= 5)).mean()
    assert off_hours_share > 0.05, 'ATO off-hours share too low'

def test_smurfing_amounts_near_threshold():
    smurfing_df = final_df[final_df['fraud_typology'] == 'smurfing']
    in_threshold = (
        (smurfing_df['amount'] >= Decimal('11000')) &
        (smurfing_df['amount'] <= Decimal('13200'))
    )
    assert in_threshold.mean() > 0.70, 'Smurfing threshold-adjacent share too low'

def test_business_impersonation_amounts_small_retail_dominant():
    business_df = final_df[final_df['fraud_typology'] == 'business_impersonation']
    amounts_float = np.array([float(a) for a in business_df['amount']])
    median = np.median(amounts_float)
    assert 500 <= median <= 5_000, 'Business median outside small_retail range'

def test_mule_to_mule_blank_concept_rate():
    mule_df = final_df[final_df['fraud_typology'] == 'mule_to_mule']
    blank_rate = (mule_df['concept_pago'] == '').mean()
    assert blank_rate > 0.78, 'Mule-to-mule blank rate too low'

def test_no_self_transactions_in_fraud():
    fraud_rows = final_df[final_df['is_fraud']]
    assert (fraud_rows['sender_account_id'] != fraud_rows['receiver_account_id']).all()

def test_referential_integrity():
    valid_ids = set(accounts_df['account_id'])
    assert final_df['sender_account_id'].isin(valid_ids).all()
    assert final_df['receiver_account_id'].isin(valid_ids).all()