import pandas as pd
from decimal import Decimal
from src.data_generator.accounts import generate_accounts
from src.data_generator.config import DEFAULT_SEED, SIMULATION_START, SIMULATION_END
from src.data_generator.transactions import generate_transactions





accounts_df = generate_accounts(10_000)
transactions_df = generate_transactions(accounts_df)

def test_generation_is_reproducible():
    df1 = generate_transactions(accounts_df, seed= DEFAULT_SEED)
    df2 = generate_transactions(accounts_df, seed= DEFAULT_SEED)
    assert df1.equals(df2)

def test_column_schema():
    columns = [
        'transaction_id', 'sender_account_id', 'sender_clabe', 'receiver_account_id', 'receiver_clabe',
        'amount', 'transaction_date', 'concept_pago', 'status', 'is_fraud', 'fraud_typology', 'fraud_event_id'
    ]
    assert list(transactions_df.columns) == columns

def test_no_self_transactions():
    assert (transactions_df['sender_account_id'] != transactions_df['receiver_account_id']).all()

def test_valid_clabes_transactions_df():
    from src.data_generator.clabe import validate_clabe
    assert transactions_df['sender_clabe'].apply(validate_clabe).all()
    assert transactions_df['receiver_clabe'].apply(validate_clabe).all()

def test_all_clabes_are_18_chars():
    assert (transactions_df['sender_clabe'].str.len() == 18).all()
    assert (transactions_df['receiver_clabe'].str.len() == 18).all()

def test_referential_integrity():
    assert transactions_df['sender_account_id'].isin(accounts_df['account_id']).all()
    assert transactions_df['receiver_account_id'].isin(accounts_df['account_id']).all()

def test_amounts_greater_than_0():
    assert (transactions_df['amount']> Decimal('0')).all()

def test_amounts_distribution_matches_banxico():
    below_threshold = (transactions_df['amount'] < Decimal('13200')).mean()
    assert abs(below_threshold -.93) < .03

def test_timestamps_within_window():
    assert (transactions_df['transaction_date'] >= pd.Timestamp(SIMULATION_START)).all()
    assert (transactions_df['transaction_date'] < pd.Timestamp(SIMULATION_END) + pd.Timedelta(days=1)).all()

def test_concept_pago_blank_rate():
    blank_concept = (transactions_df['concept_pago'] == '').mean()
    assert abs(blank_concept - .3) < .03

def test_v1_fraud_columns_as_placeholders():
    assert not transactions_df['is_fraud'].any()
    assert transactions_df['fraud_typology'].isna().all()
    assert transactions_df['fraud_event_id'].isna().all()

def test_status():
    assert (transactions_df['status'] == 'Liquidada').all()