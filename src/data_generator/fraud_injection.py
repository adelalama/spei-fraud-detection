import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

from numpy.ma.core import concatenate

from src.data_generator.config import SIMULATION_START, SIMULATION_END, DEFAULT_SEED
from src.data_generator.transactions import LEGITIMATE_CONCEPTS, generate_transactions, AMOUNT_REGIMES, HOUR_WEIGHTS, DAY_OF_WEEK_WEIGHTS, sample_amounts
from src.data_generator.accounts import generate_accounts

MULE_MAX_AGE_DAYS = 365
MULE_KYC_TIER_DISTRIBUTION = {
    1: .3,
    2: .5,
    3: .15,
    4: .05,
}

MULE_ACTIVITY_SEGMENT_DISTRIBUTION = {
    'dormant': .25,
    'light': .35,
    'regular': .25,
    'heavy': .1,
    'power': .05,
}

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

ATO_HOUR_WEIGHTS = {
    0: 8.0, 1: 7.0, 2: 6.0, 3: 6.0, 4: 7.0, 5: 7.0,
    22: 6.0, 23: 8.0,
    6: 1.5, 7: 2.0, 8: 2.5, 9: 3.0, 10: 3.5, 11: 3.0,
    12: 2.5, 13: 2.5, 14: 3.0, 15: 3.0, 16: 2.5,
    17: 2.5, 18: 2.0, 19: 2.0, 20: 2.0, 21: 1.5,
}

ATO_SEGMENT_MULTIPLIERS = {
    'dormant': 1.0,
    'light': 1.0,
    'regular': 1.0,
    'heavy': 1.5,
    'power': 2.0,
}

ATO_ESTABLISHED_PAIR_RATE = 0.22
ATO_ESTABLISHED_PAIR_MIN_COUNT = 2

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

APP_ESTABLISHED_PAIR_RATE = 0.17

APP_ESTABLISHED_PAIR_MIN_COUNT = 5

BUSINESS_AMOUNT_WEIGHTS = {'small_retail': 20, 'medium_retail': 55, 'large': 25}

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

BUSINESS_ESTABLISHED_PAIR_RATE = 0.20
BUSINESS_ESTABLISHED_PAIR_MIN_COUNT = 2

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

SMURFING_AMOUNT_MODE_PROBS = [.55, .35, .1]

SMURFING_THRESHOLD_RANGE = (11_000, 13_199)
SMURFING_MIXED_RANGE = (6_000, 10_999)

SMURFING_RECEIVER_COUNT_PROBS = [0.60, 0.30, 0.10]

SMURFING_TIMING_PROBS = [0.60, 0.30, 0.10]
SMURFING_TIMING_WINDOWS_HOURS = [24, 72, 96]
SMURFING_NOISE_RANGE = (15_000, 30_000)

SMURFING_ESTABLISHED_PAIR_RATE = 0.35
SMURFING_ESTABLISHED_PAIR_MIN_COUNT = 3

MULE_AMOUNT_WEIGHTS = {
    'medium_retail': 40,
    'small_retail': 30,
    'large': 20,
    'micro': 10,
}

MULE_TO_MULE_SPLIT = 0.50
MULE_CONCEPT_BLANK_RATE = 0.85

FRAUD_RATE = 0.015

TYPOLOGY_MIX = {
    'app_fraud': 0.35,
    'ato': 0.27,
    'mule_to_mule': 0.20,
    'smurfing': 0.10,
    'business_impersonation': 0.08,
}

COLUMN_ORDER = [
        'transaction_id', 'sender_account_id', 'sender_clabe', 'receiver_account_id', 'receiver_clabe',
        'amount','transaction_date', 'concept_pago','status','is_fraud','fraud_typology','fraud_event_id'
    ]

def select_mule_accounts(accounts_df, rng):

    scale_factor = len(accounts_df)/ 10_000
    n_per_pool= {typology: int(count*scale_factor) for typology, count in MULE_POOL_COUNTS_PER_10K.items()}
    target_mules = sum(n_per_pool.values())

    age_cutoff = pd.Timestamp(SIMULATION_START - timedelta(days = MULE_MAX_AGE_DAYS))
    eligible = accounts_df[accounts_df['creation_date'] >= age_cutoff].copy()

    eligible['tier_weight'] = eligible['kyc_tier'].map(MULE_KYC_TIER_DISTRIBUTION)
    eligible['segment_weight'] = eligible['activity_segment'].map(MULE_ACTIVITY_SEGMENT_DISTRIBUTION)
    eligible['mule_weight'] = eligible['tier_weight'] * eligible['segment_weight']

    probs = eligible['mule_weight'] / eligible['mule_weight'].sum()

    if len(eligible) < target_mules:
        print(f'Warning: Only {len(eligible)} eligible accounts for {target_mules} target mules.')

    mule_sample = rng.choice(
        eligible['account_id'].values,
        size=target_mules,
        replace=False,
        p=probs.values
    )

    mule_pools = {}
    start = 0
    for typology, count in n_per_pool.items():
        mule_pools[typology] = list(mule_sample[start:start+count])

    assert sum(len(pool) for pool in mule_pools.values()) == target_mules
    for typology, pool in mule_pools.items():
        assert len(set(pool)) == len(pool)

    return mule_pools

def split_mules_into_fresh_and_cover(mule_pools, rng, fresh_rate = .3):
    """Split all mules into fresh and cover (with legitimate transaction history before fraud)"""
    all_mule_ids = np.array([aid for pool in mule_pools.values() for aid in pool])

    shuffled = rng.permutation(all_mule_ids)

    total_mules = len(shuffled)
    n_fresh = int(total_mules * fresh_rate)

    fresh_mule_ids = set(shuffled[:n_fresh])
    cover_mule_ids = set(shuffled[n_fresh:])

    return fresh_mule_ids, cover_mule_ids

def build_mule_beneficiary_networks(cover_mule_ids, accounts_df, all_mule_ids, rng):
    """Build small beneficiary networks for cover mules"""

    non_mule_pool = accounts_df[~accounts_df['account_id'].isin(all_mule_ids)]['account_id'].values

    networks = {}

    for mule_id in cover_mule_ids:
        network_size = rng.integers(3, 9)

        eligible = non_mule_pool
        network = rng.choice(eligible, size = network_size, replace = False)

        networks[mule_id] = list(network)

    return networks

def generate_mule_cover_transactions(
        cover_mule_ids,
        accounts_df,
        mule_networks,
        non_mule_pool,
        rng
):
    """Generate legitimate cover transactions for cover-mules across simulation window."""

    sender_ids_list = []
    receiver_ids_list = []
    amounts_list = []
    timestamps_list = []
    concepts_list = []

    sim_start = pd.Timestamp(SIMULATION_START)
    sim_end = pd.Timestamp(SIMULATION_END)
    window_seconds = (sim_end - sim_start).total_seconds()

    for mule_id in cover_mule_ids:
        n_cover_txns = rng.integers(10, 31)

        network = mule_networks[mule_id]
        network_rolls = rng.random(n_cover_txns)
        use_network = network_rolls < .9

        receivers = []
        for i in range(n_cover_txns):
            if use_network[i]:
                receivers.append(rng.choice(network))
            else:
                receivers.append(rng.choice(non_mule_pool))

        offset_seconds = rng.uniform(0, window_seconds, size=n_cover_txns)
        timestamps = sim_start + pd.to_timedelta(offset_seconds, unit='s')

        mule_tier = accounts_df.loc[accounts_df['account_id'] == mule_id, 'kyc_tier'].values[0]
        mule_tiers = np.full(n_cover_txns, mule_tier)
        amounts = sample_amounts(n_cover_txns, rng, sender_tiers=mule_tiers)

        concept_names = list(LEGITIMATE_CONCEPTS.keys())
        concept_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
        concept_probs = concept_weights / concept_weights.sum()
        concepts = rng.choice(concept_names, size=n_cover_txns, p=concept_probs)

        sender_ids_list.extend([mule_id] * n_cover_txns)
        receiver_ids_list.extend(receivers)
        amounts_list.extend(amounts)
        timestamps_list.extend(timestamps)
        concepts_list.extend(concepts)

    cover_df = pd.DataFrame({
        'sender_account_id': sender_ids_list,
        'receiver_account_id': receiver_ids_list,
        'amount': amounts_list,
        'transaction_date': timestamps_list,
        'concept_pago': concepts_list,
    })

    cover_df = cover_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'sender_account_id', 'clabe': 'sender_clabe'}),
        on='sender_account_id', how='left'
    )

    cover_df = cover_df.merge(
        accounts_df[['account_id', 'clabe']].rename(
            columns={'account_id': 'receiver_account_id', 'clabe': 'receiver_clabe'}),
        on='receiver_account_id', how='left'
    )

    cover_df['status'] = 'Liquidada'
    cover_df['is_fraud'] = False
    cover_df['fraud_typology'] = None
    cover_df['fraud_event_id'] = None
    cover_df['transaction_id'] = -1

    column_order = [
        'transaction_id', 'sender_account_id', 'sender_clabe',
        'receiver_account_id', 'receiver_clabe', 'amount',
        'transaction_date', 'concept_pago', 'status',
        'is_fraud', 'fraud_typology', 'fraud_event_id'
    ]
    cover_df = cover_df[column_order]

    return cover_df




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

def sample_fraud_timestamps(n, hour_multipliers, rng, hour_weights_override = None):
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
    if hour_weights_override is not None:
        adjusted_hour_rates = np.array([hour_weights_override[h] for h in range(24)])
    else:
        adjusted_hour_rates = np.array([HOUR_WEIGHTS[h] * hour_multipliers.get(h, 1.0) for h in range(24)])
    hour_probs = adjusted_hour_rates / adjusted_hour_rates.sum()
    sampled_hours = rng.choice(24, size = n, p = hour_probs)


    #seconds/min
    sampled_minutes = rng.integers(0, 60, size=n)
    sampled_seconds = rng.integers(0, 60, size=n)

    timestamps = (pd.to_datetime(sampled_dates) + pd.to_timedelta(sampled_hours, unit='h') + pd.to_timedelta(
        sampled_minutes, unit='m') + pd.to_timedelta(sampled_seconds, unit='s'))

    return timestamps


def generate_app_fraud(accounts_df, transactions_df, mule_pool, target_count, pair_counts, rng):
    """Generate APP fraud transactions.
    """

    # F1: split events into established-pair vs new-pair buckets
    established_rate = APP_ESTABLISHED_PAIR_RATE  # 0.17
    pair_min_count = APP_ESTABLISHED_PAIR_MIN_COUNT  # 5

    n_to_sample = target_count
    n_established = int(n_to_sample * established_rate)
    n_new = n_to_sample - n_established

    sender_counts = transactions_df.groupby('sender_account_id').size()
    qualifying_senders = sender_counts[sender_counts >= 10].index

    n_new_actual = min(n_new, len(qualifying_senders))
    new_victim_ids = rng.choice(qualifying_senders, size=n_new_actual, replace=False)
    new_receiver_ids = rng.choice(mule_pool, size=n_new_actual)

    app_pairs_pool = pair_counts[pair_counts['pair_txn_count'] >= pair_min_count]

    n_established_actual = min(n_established, len(app_pairs_pool))

    if n_established_actual > 0:
        sampled_pairs = app_pairs_pool.sample(n=n_established_actual, random_state=rng.integers(0, 2 ** 31))
        established_victim_ids = sampled_pairs['sender_account_id'].values
        established_receiver_ids = sampled_pairs['receiver_account_id'].values
    else:
        established_victim_ids = np.array([], dtype=int)
        established_receiver_ids = np.array([], dtype=int)

    victim_ids = np.concatenate([new_victim_ids, established_victim_ids])
    receiver_ids = np.concatenate([new_receiver_ids, established_receiver_ids])
    actual_total = len(victim_ids)

    app_amounts = sample_fraud_amounts(actual_total, APP_AMOUNT_WEIGHTS, rng)

    timestamps = sample_fraud_timestamps(actual_total, {}, rng)

    app_vocab_use = rng.random(actual_total) < .6
    app_vocab_names = list(APP_FRAUD_VOCAB.keys())
    app_vocab_weights = np.array(list(APP_FRAUD_VOCAB.values()))

    n_fraud_concepts = app_vocab_use.sum()
    concept_probs = app_vocab_weights / app_vocab_weights.sum()
    assign_fraud_concept = rng.choice(app_vocab_names, p=concept_probs, size=n_fraud_concepts)

    legit_names = list(LEGITIMATE_CONCEPTS.keys())
    legit_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
    legit_probs = legit_weights / legit_weights.sum()

    n_legit_concepts = (~app_vocab_use).sum()
    assign_legit_concepts = rng.choice(legit_names, p=legit_probs, size=n_legit_concepts)

    concepts = np.empty(actual_total, dtype=object)
    concepts[app_vocab_use] = assign_fraud_concept
    concepts[~app_vocab_use] = assign_legit_concepts

    fraud_df = pd.DataFrame({
        "sender_account_id": victim_ids,
        "receiver_account_id": receiver_ids,
        "amount": app_amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud": True,
        "fraud_typology": 'app_fraud',
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


def generate_business_impersonation(accounts_df, transactions_df, mule_pool, target_count, pair_counts, rng):
    """Generate business impersonation fraud transactions"""

    established_rate = BUSINESS_ESTABLISHED_PAIR_RATE  # 0.20
    pair_min_count = BUSINESS_ESTABLISHED_PAIR_MIN_COUNT  # 2

    n_to_sample = target_count
    n_established = int(n_to_sample * established_rate)
    n_new = n_to_sample - n_established

    sender_counts = transactions_df.groupby('sender_account_id').size()
    qualifying_senders = sender_counts[sender_counts >= 10].index

    n_new_actual = min(n_new, len(qualifying_senders))
    new_victim_ids = rng.choice(qualifying_senders, size=n_new_actual, replace=False)
    new_receiver_ids = rng.choice(mule_pool, size=n_new_actual)

    biz_pairs_pool = pair_counts[pair_counts['pair_txn_count'] >= pair_min_count]
    n_established_actual = min(n_established, len(biz_pairs_pool))

    if n_established_actual > 0:
        sampled_pairs = biz_pairs_pool.sample(n=n_established_actual, random_state=rng.integers(0, 2 ** 31))
        established_victim_ids = sampled_pairs['sender_account_id'].values
        established_receiver_ids = sampled_pairs['receiver_account_id'].values
    else:
        established_victim_ids = np.array([], dtype=int)
        established_receiver_ids = np.array([], dtype=int)

    victim_ids = np.concatenate([new_victim_ids, established_victim_ids])
    receiver_ids = np.concatenate([new_receiver_ids, established_receiver_ids])
    actual_total = len(victim_ids)

    biz_amounts = sample_fraud_amounts(actual_total, BUSINESS_AMOUNT_WEIGHTS, rng)
    timestamps = sample_fraud_timestamps(actual_total, BUSINESS_HOUR_MULTIPLIERS, rng)

    biz_vocab_use = rng.random(actual_total) < .8
    biz_vocab_names = list(BUSINESS_IMPERSONATION_VOCAB.keys())
    biz_vocab_weights = np.array(list(BUSINESS_IMPERSONATION_VOCAB.values()))
    biz_probs = biz_vocab_weights / biz_vocab_weights.sum()

    n_biz_concepts = biz_vocab_use.sum()
    assigned_biz_concepts = rng.choice(biz_vocab_names, size=n_biz_concepts, p=biz_probs)

    legit_names = list(LEGITIMATE_CONCEPTS.keys())
    legit_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
    legit_probs = legit_weights / legit_weights.sum()

    n_legit_concepts = (~biz_vocab_use).sum()
    assigned_legit_concepts = rng.choice(legit_names, size=n_legit_concepts, p=legit_probs)

    concepts = np.empty(actual_total, dtype=object)
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


def generate_ato(accounts_df, transactions_df, mule_pool, target_count, pair_counts, rng):
    """Generate ATO fraud transactions"""

    established_rate = ATO_ESTABLISHED_PAIR_RATE  # 0.22
    pair_min_count = ATO_ESTABLISHED_PAIR_MIN_COUNT  # 2

    n_events = int(target_count / 1.35)
    n_established_events = int(n_events * established_rate)
    n_new_events = n_events - n_established_events

    one_year_ago = pd.Timestamp(SIMULATION_START - timedelta(days=ATO_MIN_VICTIM_AGE_DAYS))
    established_ids = accounts_df[accounts_df['creation_date'] <= one_year_ago]

    sender_count = transactions_df.groupby('sender_account_id').size()
    active_senders = sender_count[sender_count >= 15].index

    qualifying_victims = established_ids[established_ids['account_id'].isin(active_senders)]['account_id']

    n_new_actual = min(n_new_events, len(qualifying_victims))
    new_victim_ids = rng.choice(qualifying_victims.values, size=n_new_actual, replace=False)

    ato_pairs_pool = pair_counts[pair_counts['pair_txn_count'] >= pair_min_count]
    n_established_actual = min(n_established_events, len(ato_pairs_pool))

    if n_established_actual > 0:
        sampled_pairs = ato_pairs_pool.sample(n=n_established_actual, random_state=rng.integers(0, 2 ** 31))
        established_victim_ids = sampled_pairs['sender_account_id'].values
        established_event_receivers = sampled_pairs['receiver_account_id'].values
    else:
        established_victim_ids = np.array([], dtype=int)
        established_event_receivers = np.array([], dtype=int)

    all_victim_ids = np.concatenate([new_victim_ids, established_victim_ids])
    is_established = np.concatenate([
        np.zeros(len(new_victim_ids), dtype=bool),
        np.ones(len(established_victim_ids), dtype=bool)
    ])
    actual_total_events = len(all_victim_ids)

    n_transactions_per_event = rng.choice([1, 2, 3], size=actual_total_events, p=ATO_TRANSACTIONS_PER_EVENT_PROBS)
    sender_ids_expanded = np.repeat(all_victim_ids, n_transactions_per_event)
    event_ids_expanded = np.repeat(np.arange(actual_total_events), n_transactions_per_event)
    is_established_expanded = np.repeat(is_established, n_transactions_per_event)
    n_total_transactions = len(sender_ids_expanded)

    receiver_ids = np.empty(n_total_transactions, dtype=int)

    new_mask = ~is_established_expanded
    receiver_ids[new_mask] = rng.choice(mule_pool, size=new_mask.sum())

    for event_idx in range(len(new_victim_ids), actual_total_events):
        event_mask = event_ids_expanded == event_idx
        established_event_idx = event_idx - len(new_victim_ids)
        receiver_ids[event_mask] = established_event_receivers[established_event_idx]

    ato_amounts = sample_fraud_amounts(n_total_transactions, ATO_AMOUNT_WEIGHTS, rng)

    segment_map = accounts_df.set_index('account_id')['activity_segment'].to_dict()
    sender_segments = [segment_map[s] for s in sender_ids_expanded]
    multipliers = np.array([ATO_SEGMENT_MULTIPLIERS[seg] for seg in sender_segments])
    ato_amounts = [Decimal(str(round(float(a) * m, 2))) for a, m in zip(ato_amounts, multipliers)]

    timestamps = sample_fraud_timestamps(n_total_transactions, {}, rng, hour_weights_override=ATO_HOUR_WEIGHTS)

    roll = rng.random(n_total_transactions)
    generic = (roll >= .8) & (roll < .95)
    fraud = roll >= .95

    concepts = np.full(n_total_transactions, "", dtype=object)

    n_generic = generic.sum()
    if n_generic > 0:
        generic_names = list(ATO_GENERIC_CONCEPTS.keys())
        generic_weights = np.array(list(ATO_GENERIC_CONCEPTS.values()))
        generic_probs = generic_weights / generic_weights.sum()
        concepts[generic] = rng.choice(generic_names, size=n_generic, p=generic_probs)

    n_fraud = fraud.sum()
    if n_fraud > 0:
        fraud_names = list(APP_FRAUD_VOCAB.keys())
        fraud_weights = np.array(list(APP_FRAUD_VOCAB.values()))
        fraud_probs = fraud_weights / fraud_weights.sum()
        concepts[fraud] = rng.choice(fraud_names, size=n_fraud, p=fraud_probs)

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


def generate_smurfing(accounts_df, transactions_df, mule_pool, target_count, pair_counts, rng):
    """Generate smurfing fraud transactions"""

    established_rate = SMURFING_ESTABLISHED_PAIR_RATE  # 0.35
    pair_min_count = SMURFING_ESTABLISHED_PAIR_MIN_COUNT  # 3

    sender_counts = transactions_df.groupby('sender_account_id').size()
    active_senders = sender_counts[sender_counts >= 15].index

    n_events = int(target_count / 6)
    n_established_events = int(n_events * established_rate)
    n_new_events = n_events - n_established_events

    n_new_actual = min(n_new_events, len(active_senders))
    new_perpetrator_ids = rng.choice(active_senders, size=n_new_actual, replace=False)

    smurfing_pairs_pool = pair_counts[pair_counts['pair_txn_count'] >= pair_min_count]
    n_established_actual = min(n_established_events, len(smurfing_pairs_pool))

    if n_established_actual > 0:
        sampled_pairs = smurfing_pairs_pool.sample(n=n_established_actual, random_state=rng.integers(0, 2 ** 31))
        established_perpetrator_ids = sampled_pairs['sender_account_id'].values
        established_event_receivers = sampled_pairs['receiver_account_id'].values
    else:
        established_perpetrator_ids = np.array([], dtype=int)
        established_event_receivers = np.array([], dtype=int)

    all_perpetrator_ids = np.concatenate([new_perpetrator_ids, established_perpetrator_ids])
    is_established = np.concatenate([
        np.zeros(len(new_perpetrator_ids), dtype=bool),
        np.ones(len(established_perpetrator_ids), dtype=bool)
    ])
    actual_total_events = len(all_perpetrator_ids)

    min_size, max_size = SMURFING_EVENT_SIZE_RANGE
    event_sizes = rng.integers(min_size, max_size + 1, size=actual_total_events)

    sender_ids_expanded = np.repeat(all_perpetrator_ids, event_sizes)
    event_ids = np.repeat(np.arange(actual_total_events), event_sizes)
    is_established_expanded = np.repeat(is_established, event_sizes)

    receivers_per_event = rng.choice([1, 2, 3], size=actual_total_events, p=SMURFING_RECEIVER_COUNT_PROBS)

    receiver_lists = []
    for i in range(actual_total_events):
        n_transactions_this_event = event_sizes[i]

        if is_established[i]:
            established_event_idx = i - len(new_perpetrator_ids)
            single_receiver = established_event_receivers[established_event_idx]
            txn_receivers = np.full(n_transactions_this_event, single_receiver)
        else:
            n_receivers = receivers_per_event[i]
            event_receivers = rng.choice(mule_pool, size=n_receivers, replace=False)
            txn_receivers = rng.choice(event_receivers, size=n_transactions_this_event)

        receiver_lists.append(txn_receivers)

    receiver_ids = np.concatenate(receiver_lists)

    n_total_transactions = len(sender_ids_expanded)

    modes = rng.choice(['threshold', 'below', 'noise'],
                       size=n_total_transactions,
                       p=SMURFING_AMOUNT_MODE_PROBS)

    amounts_float = np.empty(n_total_transactions)

    threshold_mask = modes == 'threshold'
    if threshold_mask.sum() > 0:
        low, high = SMURFING_THRESHOLD_RANGE
        amounts_float[threshold_mask] = rng.uniform(low, high + 1, size=threshold_mask.sum())

    below_mask = modes == 'below'
    if below_mask.sum() > 0:
        low, high = SMURFING_MIXED_RANGE
        amounts_float[below_mask] = rng.uniform(low, high + 1, size=below_mask.sum())

    noise_mask = modes == 'noise'
    if noise_mask.sum() > 0:
        low, high = SMURFING_NOISE_RANGE
        amounts_float[noise_mask] = rng.uniform(low, high + 1, size=noise_mask.sum())

    amounts_rounded = np.round(amounts_float, 2)
    amounts = [Decimal(str(x)) for x in amounts_rounded]

    window_hours_per_event = rng.choice(SMURFING_TIMING_WINDOWS_HOURS, size=actual_total_events,
                                        p=SMURFING_TIMING_PROBS)

    sim_start_ts = pd.Timestamp(SIMULATION_START)
    sim_end_ts = pd.Timestamp(SIMULATION_END) + pd.Timedelta(days=1)

    sim_end_seconds = (sim_end_ts - sim_start_ts).total_seconds()
    window_seconds_per_event = window_hours_per_event * 3600

    latest_start_per_event = sim_end_seconds - window_seconds_per_event
    burst_start = rng.uniform(0, latest_start_per_event, size=actual_total_events)

    burst_start_expanded = np.repeat(burst_start, event_sizes)
    window_expanded = np.repeat(window_seconds_per_event, event_sizes)

    offset_seconds = rng.uniform(0, window_expanded, size=n_total_transactions)
    timestamps_seconds = burst_start_expanded + offset_seconds
    timestamps = sim_start_ts + pd.to_timedelta(timestamps_seconds, unit='s')

    roll = rng.random(n_total_transactions)
    is_generic = (roll >= .6) & (roll < .9)
    is_varied = roll >= .9

    concepts = np.full(n_total_transactions, "", dtype=object)

    n_generic = is_generic.sum()
    if n_generic > 0:
        generic_names = list(ATO_GENERIC_CONCEPTS.keys())
        generic_weights = np.array(list(ATO_GENERIC_CONCEPTS.values()))
        generic_probs = generic_weights / generic_weights.sum()
        concepts[is_generic] = rng.choice(generic_names, size=n_generic, p=generic_probs)

    n_varied = is_varied.sum()
    if n_varied > 0:
        varied_names = list(LEGITIMATE_CONCEPTS.keys())
        varied_weights = np.array(list(LEGITIMATE_CONCEPTS.values()))
        varied_probs = varied_weights / varied_weights.sum()
        concepts[is_varied] = rng.choice(varied_names, size=n_varied, p=varied_probs)

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

def generate_mule_to_mule(mule_pools, accounts_df, target_count, rng):
    """Generate mule_to_mule and mule cash out fraud transactions"""

    all_mules = np.concatenate([mule_pools['app'], mule_pools['ato'], mule_pools['business'], mule_pools['shared']])

    n_total_transactions = target_count

    sender_ids = rng.choice(all_mules, size = n_total_transactions)
    is_mule_to_mule = rng.random(n_total_transactions) < MULE_TO_MULE_SPLIT

    mule_to_mule_receivers = rng.choice(all_mules, size = is_mule_to_mule.sum())

    all_accounts_ids = accounts_df['account_id'].values
    cash_out_receivers = rng.choice(all_accounts_ids, size = (~is_mule_to_mule).sum())

    receiver_ids = np.empty(n_total_transactions, dtype = int)
    receiver_ids[is_mule_to_mule] = mule_to_mule_receivers
    receiver_ids[~is_mule_to_mule] = cash_out_receivers

    self_collisions = sender_ids == receiver_ids
    n_collisions = self_collisions.sum()
    if n_collisions > 0:
        receiver_ids[self_collisions] = rng.choice(all_accounts_ids, size = n_collisions)


    amounts = sample_fraud_amounts(n_total_transactions, MULE_AMOUNT_WEIGHTS, rng)

    timestamps = sample_fraud_timestamps(n_total_transactions, {}, rng)

    concepts = np.full(n_total_transactions, "", dtype = object)
    roll = rng.random(n_total_transactions)
    is_generic = roll >= MULE_CONCEPT_BLANK_RATE

    n_generic = is_generic.sum()
    if n_generic > 0:
        generic_names = list(ATO_GENERIC_CONCEPTS.keys())
        generic_weights = np.array(list(ATO_GENERIC_CONCEPTS.values()))
        generic_probs = generic_weights / generic_weights.sum()
        concepts[is_generic] = rng.choice(generic_names, size=n_generic, p=generic_probs)

    event_ids = np.arange(n_total_transactions)

    fraud_df = pd.DataFrame({
        "sender_account_id": sender_ids,
        "receiver_account_id": receiver_ids,
        "amount": amounts,
        "transaction_date": timestamps,
        "concept_pago": concepts,
        "is_fraud": True,
        "fraud_typology": 'mule_to_mule',
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


def inject_fraud(transactions_df, accounts_df, seed = DEFAULT_SEED):
    """Inject fraud transactions of all 5 typologies into transactions_df"""

    rng = np.random.default_rng(seed)

    target_total_fraud = int(len(transactions_df) * FRAUD_RATE)
    target_app = int(target_total_fraud * TYPOLOGY_MIX['app_fraud'])
    target_ato = int(target_total_fraud * TYPOLOGY_MIX['ato'])
    target_mule = int(target_total_fraud * TYPOLOGY_MIX['mule_to_mule'])
    target_smurfing = int(target_total_fraud * TYPOLOGY_MIX['smurfing'])
    target_business = int(target_total_fraud * TYPOLOGY_MIX['business_impersonation'])

    mule_pools = select_mule_accounts(accounts_df, rng)

    fresh_mule_ids, cover_mule_ids = split_mules_into_fresh_and_cover(mule_pools, rng)
    all_mule_ids = fresh_mule_ids | cover_mule_ids

    pair_counts = transactions_df.groupby(
        ['sender_account_id', 'receiver_account_id']
    ).size().reset_index(name='pair_txn_count')

    app_df = generate_app_fraud(accounts_df, transactions_df, mule_pools['app'], target_app, pair_counts, rng)

    business_df = generate_business_impersonation(accounts_df, transactions_df, mule_pools['business'], target_business, pair_counts, rng)

    ato_df = generate_ato(accounts_df, transactions_df, mule_pools['ato'], target_ato, pair_counts, rng)

    smurfing_df = generate_smurfing(accounts_df, transactions_df, mule_pools['shared'], target_smurfing, pair_counts, rng)

    mule_df = generate_mule_to_mule(mule_pools, accounts_df, target_mule ,rng)

    mule_networks = build_mule_beneficiary_networks(cover_mule_ids, accounts_df, all_mule_ids, rng)

    non_mule_pool = accounts_df[~accounts_df['account_id'].isin(all_mule_ids)]['account_id'].values

    cover_df = generate_mule_cover_transactions(
        cover_mule_ids,
        accounts_df,
        mule_networks,
        non_mule_pool,
        rng
    )

    offset = 0
    for df in [app_df, business_df, ato_df, smurfing_df, mule_df]:
        df['fraud_event_id'] = df['fraud_event_id'] + offset
        offset = df['fraud_event_id'].max() +1

    all_fraud_df = pd.concat([app_df, business_df, ato_df, smurfing_df, mule_df ], ignore_index=True)

    all_fraud_df['transaction_id'] = -1

    final_df = pd.concat([transactions_df, cover_df, all_fraud_df], ignore_index=True)

    final_df = final_df.sort_values('transaction_date').reset_index(drop=True)

    final_df['transaction_id'] = np.arange(len(final_df))

    final_df = final_df[COLUMN_ORDER]

    validate_fraud_injection(final_df, accounts_df)

    return final_df


def validate_fraud_injection(final_df, accounts_df):
    """Validates the adequate concatenation of combined transactions and fraud data frame"""

    #fraud rate approx target
    fraud_rate = final_df['is_fraud'].mean()
    assert .013 <= fraud_rate <= .016, 'fraud rate outside expected range'

    #valid fraud typologies
    valid_typologies = {'app_fraud', 'ato', 'mule_to_mule', 'smurfing', 'business_impersonation'}
    fraud_rows = final_df[final_df['is_fraud']]
    assert fraud_rows['fraud_typology'].isin(valid_typologies).all(), 'Invalid typology in df'

    #transaction_id sequential & unique
    assert (final_df['transaction_id'] == np.arange(len(final_df))).all(), 'transaction_id non sequential'

    #transaction chronology preserved
    assert final_df['transaction_date'].is_monotonic_increasing, 'Not chronologically sorted'

    #fraud_typologies are consistent with fraud events
    event_typology_counts = fraud_rows.groupby('fraud_event_id')['fraud_typology'].nunique()
    assert (event_typology_counts == 1).all(), 'fraud_event_id spans multiple typologies'

    #validating sender and receiver ids
    valid_ids = set(accounts_df['account_id'])
    assert final_df['sender_account_id'].isin(valid_ids).all(), 'Invalid sender IDs'
    assert final_df['receiver_account_id'].isin(valid_ids).all(), 'Invalid receiver IDs'


if __name__ == '__main__':

    accounts_df = generate_accounts(10_000)
    transactions_df = generate_transactions(accounts_df)
    rng = np.random.default_rng(DEFAULT_SEED)
    final_df = inject_fraud(transactions_df, accounts_df)

    print(f"Final number of transactions: {len(final_df)}")
    print(f"Fraud rate: {final_df['is_fraud'].mean() * 100: .2f}%")
    print(f"Typology counts:")
    print(final_df['fraud_typology'].value_counts())
