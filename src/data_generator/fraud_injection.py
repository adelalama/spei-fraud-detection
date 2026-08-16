import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from config import SIMULATION_START, SIMULATION_END, DEFAULT_SEED
from src.data_generator.transactions import LEGITIMATE_CONCEPTS, generate_transactions
from transactions import AMOUNT_REGIMES, HOUR_WEIGHTS, DAY_OF_WEEK_WEIGHTS
from src.data_generator.accounts import generate_accounts

MULE_MAX_AGE_DAYS = 365
MULE_KYC_TIERS = [1, 2]
MULE_ACTIVITY_SEGMENTS = ['dormant', 'light']
MULE_POOL_COUNTS_PER_10K = {
    'app': 55,
    'ato': 30,
    'business': 10,
    'shared': 10,
}

ATO_HOUR_MULTIPLIERS = {
    0: 5.0, 1: 5.0, 2: 5.0, 3: 5.0, 4: 5.0, 5: 5.0,
    22: 3.0, 23: 3.0,
}

BUSINESS_HOUR_MULTIPLIERS = {
    9: 1.3, 10: 1.3, 11: 1.3, 12: 1.3,
    13: 1.3, 14: 1.3, 15: 1.3, 16: 1.3, 17: 1.3,
}

APP_FRAUD_VOCAB = {
    "pago urgente": 15,
    "emergencia": 13,
    "familia": 12,
    "adelanto": 12,
    "oferta": 10,
    "inversión": 8,
    "compra iPhone": 6,
    "compra auto": 5,
    "transferencia": 5,
    "compra": 4,
    "": 10,
}

APP_AMOUNT_WEIGHTS = {'medium_retail': 60, 'large':30, 'small_retail':10}

BUSINESS_AMOUNT_WEIGHTS = {'small_retail': 70, 'micro': 20, 'medium_retail': 10}

BUSINESS_IMPERSONATION_VOCAB = {
    "membresia premium": 12,
    "renovacion anual": 10,
    "comision apertura": 10,
    "servicio anual": 10,
    "factura pendiente": 12,
    "cargo mensual": 8,
    "cuota inscripcion": 8,
    "servicios profesionales": 6,
    "actualizacion cuenta": 6,
    "verificacion": 8,
    "": 10,
}

ATO_MIN_VICTIM_AGE_DAYS = 365

ATO_AMOUNT_WEIGHTS = {'large': 50, 'medium_retail': 40, 'high_value': 10}

ATO_TRANSACTIONS_PER_EVENT_PROBS = [.7, .25, .05]

ATO_GENERIC_CONCEPTS = {
    'transferencia': 40,
    'pago': 30,
    'envio': 20,
    'deposito': 10
}

SMURFING_EVENT_SIZE_RANGE = (4, 8)

SMURFING_AMOUNT_MODE_PROBS = [.8, .2]

SMURFING_THRESHOLD_RANGE = (11_000, 13_199)
SMURFING_MIXED_RANGE = (5_000, 10_999)

SMURFING_RECEIVER_COUNT_PROBS = [0.60, 0.30, 0.10]

SMURFING_TIMING_PROBS = [0.60, 0.30, 0.10]
SMURFING_TIMING_WINDOWS_HOURS = [24, 72, 96]

def select_mule_accounts(accounts_df, rng):

    scale_factor = len(accounts_df)/ 10_000
    n_per_pool= {typology: int(count*scale_factor) for typology, count in MULE_POOL_COUNTS_PER_10K.items()}
    target_mules = sum(n_per_pool.values())

    qualifying_mules = accounts_df[
         (accounts_df['creation_date']>= pd.Timestamp(SIMULATION_START - timedelta(days=MULE_MAX_AGE_DAYS))) &
         (accounts_df['kyc_tier'].isin(MULE_KYC_TIERS)) &
         (accounts_df['activity_segment'].isin(MULE_ACTIVITY_SEGMENTS))
          ]

    if len(qualifying_mules) < target_mules:
        print(f'Warning: There are only {len(qualifying_mules)} qualifying mules for the {target_mules} targeted accounts')

    mule_sample = rng.choice(qualifying_mules['account_id'].values,  size = target_mules, replace = False)

    mule_pools = {}
    start = 0
    for typology, count in n_per_pool.items():
        mule_pools[typology] = list(mule_sample[start:start+count])


    assert sum(len(pool) for pool in mule_pools.values()) == target_mules
    for typology, pool in mule_pools.items():
        assert len(set(pool)) == len(pool)

    return mule_pools

def sample_fraud_amounts(n, regime_weights, rng):
    """ Sample fraud amounts with typology specific regime weights
    Returns list of decimal amounts
    """
    regime_names = list(regime_weights.keys())
    weights = np.array(list(regime_weights.values()))
    probs = weights / weights.sum()

    assigned_regimes = rng.choice(regime_names, size = n, p = probs)
    amounts = np.empty(n)

    for regime_name in regime_weights.keys():
        mask = assigned_regimes == regime_name
        n_in_regime = mask.sum()
        if n_in_regime > 0:
            mu = AMOUNT_REGIMES[regime_name]['mu']
            sigma = AMOUNT_REGIMES[regime_name]['sigma']
            amounts[mask] = rng.lognormal(mean = mu, sigma = sigma, size = n_in_regime)

    amounts_rounded = np.round(amounts, 2)
    amounts_decimal = [Decimal(str(x)) for x in amounts_rounded]

    return amounts_decimal

def sample_fraud_timestamps(n, hour_multipliers, rng):
    """Samples timestamps for fraud transactions with hour weight modifications for distinct typologies
    Return numpy array of timestamps
    """
    dates = pd.date_range(SIMULATION_START, SIMULATION_END, freq='D')
    dow_series = pd.Series(dates.dayofweek, index=dates)

    dow_weights = dow_series.map(DAY_OF_WEEK_WEIGHTS)

    is_15th = dates.day == 15

    next_day = dates + pd.Timedelta(days=1)
    is_last_day = next_day.month != dates.month

    is_spike_day = is_15th | is_last_day
    dom_multipliers = np.where(is_spike_day, 2.0, 1.0)

    combined_weights = dow_weights * dom_multipliers

    date_probs = combined_weights / combined_weights.sum()

    sampled_dates = rng.choice(dates, size=n, p=date_probs)

    #hours
    adjusted_hour_rates = np.array([HOUR_WEIGHTS[h] * hour_multipliers.get(h, 1.0) for h in range(24)])
    hour_probs = adjusted_hour_rates / adjusted_hour_rates.sum()
    sampled_hours = rng.choice(24, size = n, p = hour_probs)

    #seconds/min
    sampled_minutes = rng.integers(0, 60, size=n)
    sampled_seconds = rng.integers(0, 60, size=n)

    timestamps = (pd.to_datetime(sampled_dates) + pd.to_timedelta(sampled_hours, unit='h') + pd.to_timedelta(
        sampled_minutes, unit='m') + pd.to_timedelta(sampled_seconds, unit='s'))

    return timestamps

def generate_app_fraud(accounts_df, transactions_df, mule_pool, target_count, rng):
    """Generate APP fraud transactions"""

    sender_counts = transactions_df.groupby('sender_account_id').size()
    qualifying_senders = sender_counts[sender_counts >= 10].index

    n_to_sample = min(target_count, len(qualifying_senders))
    victim_ids = rng.choice(qualifying_senders, size = n_to_sample, replace = False)

    #mule receiver
    receiver_ids = rng.choice(mule_pool, size = n_to_sample)

    app_amounts = sample_fraud_amounts(n_to_sample, APP_AMOUNT_WEIGHTS, rng)

    #no hour skew
    timestamps = sample_fraud_timestamps(n_to_sample, {}, rng)

    #concepto_pago 60% fraud-like 40% legit
    app_vocab_use = rng.random(n_to_sample) < .6
    app_vocab_names = list(APP_FRAUD_VOCAB.keys())
    app_vocab_weights = np.array(list(APP_FRAUD_VOCAB.values()))

    n_fraud_concepts = app_vocab_use.sum()
    concept_probs = app_vocab_weights / app_vocab_weights.sum()
    assign_fraud_concept = rng.choice(app_vocab_names, p=concept_probs, size=n_fraud_concepts)

    legit_names = list(LEGITIMATE_CONCEPTS.keys())
    legit_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
    legit_probs = legit_weights / legit_weights.sum()

    n_legit_concepts = (~app_vocab_use).sum()
    assign_legit_concepts = rng.choice(legit_names, p = legit_probs,size = n_legit_concepts)

    concepts = np.empty(n_to_sample, dtype = object)
    concepts[app_vocab_use] = assign_fraud_concept
    concepts[~app_vocab_use] = assign_legit_concepts

    fraud_df = pd.DataFrame({
        "sender_account_id": victim_ids,
        "receiver_account_id": receiver_ids,
        "amount": app_amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud" : True,
        "fraud_typology": 'app_fraud',
        "status" : "Liquidada",
        "fraud_event_id" : None
    })

    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
        columns={'account_id': 'sender_account_id', 'clabe': 'sender_clabe'}),
        on='sender_account_id',
        how='left'
    )
    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
        columns={'account_id': 'receiver_account_id', 'clabe': 'receiver_clabe'}),
        on='receiver_account_id',
        how='left'
    )

    return fraud_df


def generate_business_impersonation(accounts_df, transactions_df, mule_pool, target_count, rng):
    """ Generate business impersonation fraud transactions"""

    sender_counts = transactions_df.groupby('sender_account_id').size()
    qualifying_senders = sender_counts[sender_counts >= 10].index

    n_to_sample = min(target_count, len(qualifying_senders))
    victim_ids = rng.choice(qualifying_senders, size=n_to_sample, replace=False)

    receiver_ids = rng.choice(mule_pool, size=n_to_sample)

    biz_amounts = sample_fraud_amounts(n_to_sample, BUSINESS_AMOUNT_WEIGHTS, rng)

    timestamps = sample_fraud_timestamps(n_to_sample, BUSINESS_HOUR_MULTIPLIERS, rng)

    biz_vocab_use = rng.random(n_to_sample) < .8
    biz_vocab_names = list(BUSINESS_IMPERSONATION_VOCAB.keys())
    biz_vocab_weights = np.array(list(BUSINESS_IMPERSONATION_VOCAB.values()))
    biz_probs = biz_vocab_weights / biz_vocab_weights.sum()

    n_biz_concepts = biz_vocab_use.sum()
    assigned_biz_concepts = rng.choice(biz_vocab_names, size = n_biz_concepts, p = biz_probs)

    legit_names = list(LEGITIMATE_CONCEPTS.keys())
    legit_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
    legit_probs = legit_weights / legit_weights.sum()

    n_legit_concepts = (~biz_vocab_use).sum()
    assigned_legit_concepts = rng.choice(legit_names, size = n_legit_concepts, p = legit_probs)

    concepts = np.empty(n_to_sample, dtype = object)
    concepts[biz_vocab_use] = assigned_biz_concepts
    concepts[~biz_vocab_use] = assigned_legit_concepts

    fraud_df = pd.DataFrame({
        "sender_account_id": victim_ids,
        "receiver_account_id": receiver_ids,
        "amount": biz_amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud": True,
        "fraud_typology": 'business_impersonation',
        "status": "Liquidada",
        "fraud_event_id": None
    })

    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'sender_account_id', 'clabe': 'sender_clabe'}),
        on='sender_account_id',
        how='left'
    )
    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'receiver_account_id', 'clabe': 'receiver_clabe'}),
        on='receiver_account_id',
        how='left'
    )

    return fraud_df


def generate_ato(accounts_df, transactions_df, mule_pool, target_count, rng):
    """Generate ATO fraud transactions"""

    one_year_ago = pd.Timestamp(SIMULATION_START - timedelta(days = ATO_MIN_VICTIM_AGE_DAYS))
    established_ids = accounts_df[accounts_df['creation_date'] <= one_year_ago]

    sender_count = transactions_df.groupby('sender_account_id').size()
    active_senders = sender_count[sender_count >= 15].index

    qualifying_victims = established_ids[established_ids['account_id'].isin(active_senders)]['account_id']

    n_events = int(target_count / 1.35)
    n_to_sample = min(n_events, len(qualifying_victims))
    victim_ids = rng.choice(qualifying_victims.values, size = n_to_sample, replace=False)

    n_transactions_per_event = rng.choice([1, 2, 3], size = n_to_sample, p = ATO_TRANSACTIONS_PER_EVENT_PROBS)

    sender_ids_expanded = np.repeat(victim_ids, n_transactions_per_event)
    event_ids_expanded = np.repeat(np.arange(n_to_sample), n_transactions_per_event)

    n_total_transactions = len(sender_ids_expanded)
    receiver_ids = rng.choice(mule_pool, size = n_total_transactions)

    ato_amounts = sample_fraud_amounts(n_total_transactions, ATO_AMOUNT_WEIGHTS, rng)

    timestamps = sample_fraud_timestamps(n_total_transactions, ATO_HOUR_MULTIPLIERS, rng)


    roll = rng.random(n_total_transactions)
    generic = (roll >= .8) & (roll < .95)
    fraud = roll >= .95

    concepts = np.full(n_total_transactions, "", dtype = object)

    n_generic = generic.sum()
    if n_generic > 0:
        generic_names = list(ATO_GENERIC_CONCEPTS.keys())
        generic_weights = np.array(list(ATO_GENERIC_CONCEPTS.values()))
        generic_probs = generic_weights / generic_weights.sum()
        concepts[generic] = rng.choice(generic_names, size = n_generic, p = generic_probs)

    n_fraud = fraud.sum()
    if n_fraud > 0:
        fraud_names = list(APP_FRAUD_VOCAB.keys())
        fraud_weights = np.array(list(APP_FRAUD_VOCAB.values()))
        fraud_probs = fraud_weights/ fraud_weights.sum()
        concepts[fraud] = rng.choice(fraud_names, size = n_fraud, p = fraud_probs)

    fraud_df = pd.DataFrame({
        "sender_account_id": sender_ids_expanded,
        "receiver_account_id": receiver_ids,
        "amount": ato_amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud": True,
        "fraud_typology": 'ato',
        "status": "Liquidada",
        "fraud_event_id": event_ids_expanded
    })



    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'sender_account_id', 'clabe': 'sender_clabe'}),
        on='sender_account_id',
        how='left'
    )
    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'receiver_account_id', 'clabe': 'receiver_clabe'}),
        on='receiver_account_id',
        how='left'
    )

    return fraud_df

def generate_smurfing(accounts_df, transactions_df, mule_pool, target_count, rng):
    """Generate smurfing fraud transactions"""

    sender_counts = transactions_df.groupby('sender_account_id').size()
    active_senders = sender_counts[sender_counts >= 15].index

    n_events = int(target_count / 6) # 6 = avg event size
    n_to_sample = min(n_events, len(active_senders))

    perpetrator_ids = rng.choice(active_senders, size = n_to_sample, replace = False)

    min_size, max_size = SMURFING_EVENT_SIZE_RANGE
    event_sizes = rng.integers(min_size, max_size + 1, size = n_to_sample)

    sender_ids_expanded = np.repeat(perpetrator_ids, event_sizes)
    event_ids = np.repeat(np.arange(n_to_sample), event_sizes)

    receivers_per_event = rng.choice([1, 2, 3], size= n_to_sample, p = SMURFING_RECEIVER_COUNT_PROBS)

    #multi-receiver assignments per event
    receiver_lists = []
    for i in range(n_events):
        n_receivers = receivers_per_event[i]
        n_transactions_this_event = event_sizes[i]

        event_receivers = rng.choice(mule_pool, size = n_receivers, replace = False)

        txn_receivers = rng.choice(event_receivers, size = n_transactions_this_event)
        receiver_lists.append(txn_receivers)

    receiver_ids = np.concatenate(receiver_lists)

    #amount sampling
    n_total_transactions = len(sender_ids_expanded)

    mode_roll = rng.random(n_total_transactions)
    is_threshold_mode = mode_roll < .8

    amounts_float = np.empty(n_total_transactions)

    n_threshold = is_threshold_mode.sum()
    if n_threshold > 0:
        low, high = SMURFING_THRESHOLD_RANGE
        amounts_float[is_threshold_mode] = rng.uniform(low, high +1, size = n_threshold)

    n_mixed = (~is_threshold_mode).sum()
    if n_mixed > 0:
        low, high = SMURFING_MIXED_RANGE
        amounts_float[~is_threshold_mode] = rng.uniform(low, high +1, size = n_mixed)

    amounts_rounded = np.round(amounts_float, 2)
    amounts = [Decimal(str(x)) for x in amounts_rounded]

    #transactions burst timing
    window_hours_per_event = rng.choice(SMURFING_TIMING_WINDOWS_HOURS, size = n_to_sample, p = SMURFING_TIMING_PROBS)

    sim_start_ts = pd.Timestamp(SIMULATION_START)
    sim_end_ts = pd.Timestamp(SIMULATION_END) + pd.Timedelta(days=1)

    sim_end_seconds = (sim_end_ts - sim_start_ts).total_seconds()
    window_seconds_per_event = window_hours_per_event *3600

    latest_start_per_event = sim_end_seconds - window_seconds_per_event

    burst_start = rng.uniform(0, latest_start_per_event, size = n_to_sample)

    burst_start_expanded = np.repeat(burst_start, event_sizes)
    window_expanded = np.repeat(window_seconds_per_event, event_sizes)

    offset_seconds = rng.uniform(0, window_expanded, size = n_total_transactions)

    timestamps_seconds = burst_start_expanded + offset_seconds

    timestamps = sim_start_ts + pd.to_timedelta(timestamps_seconds, unit = 's')

    roll = rng.random(n_total_transactions)
    is_generic = (roll >= .6) & (roll < .9)
    is_varied = roll >= .9

    concepts = np.full(n_total_transactions, "", dtype = object)

    n_generic = is_generic.sum()
    if n_generic > 0:
        generic_names = list(ATO_GENERIC_CONCEPTS.keys())
        generic_weights = np.array(list(ATO_GENERIC_CONCEPTS.values()))
        generic_probs = generic_weights / generic_weights.sum()
        concepts[is_generic] = rng.choice(generic_names, size = n_generic, p = generic_probs)

    n_varied = is_varied.sum()
    if n_varied > 0:
        varied_names = list(LEGITIMATE_CONCEPTS.keys())
        varied_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
        varied_probs = varied_weights / varied_weights.sum()
        concepts[is_varied] = rng.choice(varied_names, size = n_varied, p = varied_probs)

    fraud_df = pd.DataFrame({
        "sender_account_id": sender_ids_expanded,
        "receiver_account_id": receiver_ids,
        "amount": amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud": True,
        "fraud_typology": 'smurfing',
        "status": "Liquidada",
        "fraud_event_id": event_ids
    })

    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'sender_account_id', 'clabe': 'sender_clabe'}),
        on='sender_account_id',
        how='left'
    )
    fraud_df = fraud_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'receiver_account_id', 'clabe': 'receiver_clabe'}),
        on='receiver_account_id',
        how='left'
    )

    return fraud_df




if __name__ == '__main__':

    accounts_df = generate_accounts(10_000)
    transactions_df = generate_transactions(accounts_df)
    rng = np.random.default_rng(DEFAULT_SEED)

    mule_pools = select_mule_accounts(accounts_df, rng)

    app_fraud_df = generate_app_fraud(accounts_df, transactions_df, mule_pools['app'], 1130, rng)
    print(f"Generated {len(app_fraud_df)} APP fraud transactions")

    business_fraud_df = generate_business_impersonation(accounts_df, transactions_df, mule_pools['business'], 260, rng)
    print(f"Generated {len(business_fraud_df)} business impersonation transactions")

    ato_fraud_df = generate_ato(accounts_df, transactions_df, mule_pools['ato'], 870, rng)
    print(f"Generated {len(ato_fraud_df)} ATO fraud transactions")


    smurfing_df = generate_smurfing(accounts_df, transactions_df, mule_pools['shared'], 325, rng)
    print(f"Generated {len(smurfing_df)} smurfing transactions")
