import pandas as pd
import numpy as np
from datetime import timedelta
from decimal import Decimal

from src.data_generator.config import SIMULATION_START, SIMULATION_END, DEFAULT_SEED
from src.data_generator.institutions import institutions

POISSON_RATES = {
    'dormant': 1,
    'light': 8,
    'regular': 30,
    'heavy': 90,
    'power': 300,
}

NETWORK_SIZES = {
    'dormant': (1, 2),
    'light': (2, 5),
    'regular': (5, 15),
    'heavy': (15, 40),
    'power': (40, 100),
}

AMOUNT_REGIMES = {
    'micro':         {'weight': 30, 'mu': 4.4,  'sigma': 0.9},
    'small_retail':  {'weight': 40, 'mu': 7.4,  'sigma': 0.75},
    'medium_retail': {'weight': 24, 'mu': 8.7,  'sigma': 0.5},
    'large':         {'weight': 4,  'mu': 10.1, 'sigma': 1.0},
    'high_value':    {'weight': 2,  'mu': 12.7, 'sigma': 1.2},
}

DAY_OF_WEEK_WEIGHTS = {
    0: 5,
    1: 5,
    2: 5,
    3: 5,
    4: 5,
    5: 3,
    6: 2,
}

HOUR_WEIGHTS = {
    0: 0.5,
    1: 0.3,
    2: 0.2,
    3: 0.2,
    4: 0.3,
    5: 0.7,
    6: 1.5,
    7: 3.0,
    8: 6.0,
    9: 8.0,
    10: 9.0,
    11: 8.0,
    12: 5.0,
    13: 4.5,
    14: 7.0,
    15: 8.0,
    16: 7.5,
    17: 6.5,
    18: 5.0,
    19: 4.5,
    20: 4.0,
    21: 3.0,
    22: 2.0,
    23: 1.0,
}


def generate_transactions(accounts_df, seed = DEFAULT_SEED):
    """
    Generates transactions dataset from accounts_df.

    Returns tuple with final df elements
    """

    rng = np.random.default_rng(seed)

    #transaction counts per account
    base_rates = accounts_df['activity_segment'].map(POISSON_RATES)

    sim_end = pd.Timestamp(SIMULATION_END)
    day_diff = (sim_end - accounts_df['creation_date']).dt.days
    fraction = (day_diff / 180).clip(lower=0, upper=1)
    adjusted_rate = base_rates * fraction
    n_transactions = rng.poisson(adjusted_rate)

    #benefeciary networks
    beneficiary_networks = build_beneficiary_networks(accounts_df, rng)

    #transaction senders
    sender_ids = np.repeat(accounts_df['account_id'].values, n_transactions)

    #receivers
    receiver_ids = assign_transaction_receiver(sender_ids, beneficiary_networks, accounts_df, rng)

    #amounts
    amounts = sample_amounts(len(sender_ids), rng)

    #timestamps
    timestamps = sample_timestamps(len(sender_ids), rng)

    return (n_transactions, sender_ids, beneficiary_networks, receiver_ids, amounts, timestamps)


#function to build network of recurring transactions for each account
def build_beneficiary_networks(accounts_df, rng):
    """
    Build beneficiary networks for each account with a 70/30 same segment bias

    Returns dictionary mapping account_id to list of beneficiary networks account_id
    """
    accounts_by_segment = accounts_df.groupby('activity_segment')['account_id'].apply(list).to_dict()
    all_accounts_ids = accounts_df["account_id"].tolist()
    beneficiary_networks = {}

    for account_id, segment in zip(accounts_df['account_id'], accounts_df['activity_segment']):
        min_size, max_size = NETWORK_SIZES[segment]
        network_size = rng.integers(min_size, max_size +1)

        n_same = round(network_size * .7)
        n_any = network_size - n_same

        same_segment_pool = accounts_by_segment[segment]
        same_segment_sample = rng.choice(same_segment_pool, size= n_same, replace=False)

        any_segment_sample = rng.choice(all_accounts_ids, size = n_any, replace=False )

        combined = list(same_segment_sample) + list(any_segment_sample)
        if account_id in combined:
            combined = [i for i in combined if i != account_id]

        #edge case for small networks if self was only sample
        if len(combined) == 0:
            candidate = account_id
            while candidate == account_id:
                candidate = rng.choice(all_accounts_ids)
            combined = [int(candidate)]

        beneficiary_networks[account_id] = combined

    for aid, network in beneficiary_networks.items():
        assert len(network) > 0
        assert aid not in network

    return beneficiary_networks

def sample_new_beneficiary(sender_id, sender_segment, existing_network, accounts_by_segment, all_account_ids, rng):
    """Samples a new beneficiary for a sender, excludes existing network and self

     Returns one account_id
     """
    #same segment
    if rng.random()<.7:
        candidates = accounts_by_segment[sender_segment]
    else:
        candidates = all_account_ids

    excluded = set(existing_network).union({sender_id})
    eligible =[i for i in candidates if i not in excluded]

    return rng.choice(eligible)

def assign_transaction_receiver(sender_ids, beneficiary_networks, accounts_df, rng):
    """For each transaction, assigns a receiver account. 90% from senders network, 10% new beneficiary that is added to network

    Returns an array of receiver ids, equivalent to sender_ids.
    """
    all_account_ids = accounts_df["account_id"].tolist()
    accounts_by_segment = accounts_df.groupby('activity_segment')['account_id'].apply(list).to_dict()
    segment_lookup = dict(zip(accounts_df['account_id'], accounts_df['activity_segment']))

    receiver_ids = []

    for sender_id in sender_ids:
        roll = rng.random()

        if roll < .1:
            sender_segment = segment_lookup[sender_id]
            new_ben = sample_new_beneficiary(sender_id, sender_segment, beneficiary_networks[sender_id],
                                             accounts_by_segment, all_account_ids, rng)
            beneficiary_networks[sender_id].append(new_ben)
            receiver_ids.append(new_ben)
        else:
            receiver = rng.choice(beneficiary_networks[sender_id])
            receiver_ids.append(receiver)

    assert len(receiver_ids) == len(sender_ids)

    return np.array(receiver_ids)

#sampling transactions to amount regimes

def sample_amounts(n_transactions, rng):
    """
    Sample transaction amounts according to the lognormal distribution across the 5 different regimes.

    Returns list of amounts, corresponding to number of transactions.
    """
    regime_names = list(AMOUNT_REGIMES.keys())
    regime_weights = np.array([regime['weight'] for regime in AMOUNT_REGIMES.values()])
    regime_probs = regime_weights / regime_weights.sum()
    assigned_regimes = rng.choice(regime_names, p = regime_probs, size = n_transactions)

    amounts = np.empty(n_transactions)
    for regime_name, params in AMOUNT_REGIMES.items():
        mask = assigned_regimes == regime_name
        n_in_regime = mask.sum()
        if n_in_regime > 0:
            amounts[mask] = rng.lognormal(mean = params['mu'], sigma= params['sigma'], size = n_in_regime )
    amounts_rounded = np.round(amounts, 2)
    amounts_decimal = [Decimal(str(x)) for x in amounts_rounded]
    assert len(amounts_decimal) == n_transactions
    assert all(a > Decimal('0') for a in amounts_decimal)
    return amounts_decimal

#adding sampled timestamps to each transaction
def sample_timestamps(n_transactions, rng):
    """
    Sample transaction timestamps for day of month, day of week and hour patterns according to probable account activity

    Returns DateTimeIndex of length equal to n_transactions.
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

    sampled_dates = rng.choice(dates, size=n_transactions, p=date_probs)

    # hour sampling
    hour_weights_array = np.array([HOUR_WEIGHTS[h] for h in range(24)])
    hour_probs = hour_weights_array / hour_weights_array.sum()
    sampled_hours = rng.choice(24, size=n_transactions, p=hour_probs)

    # second/minute sampling
    sampled_minutes = rng.integers(0, 60, size=n_transactions)
    sampled_seconds = rng.integers(0, 60, size=n_transactions)

    timestamps = (pd.to_datetime(sampled_dates) + pd.to_timedelta(sampled_hours, unit='h') + pd.to_timedelta(sampled_minutes, unit='m')
                  + pd.to_timedelta(sampled_seconds, unit='s'))

    assert len(timestamps) == n_transactions
    return timestamps



if __name__ == "__main__":
    from src.data_generator.accounts import generate_accounts
    rng = np.random.default_rng(DEFAULT_SEED)

    accounts_df = generate_accounts(10_000)
    n_transactions, sender_ids, networks, receiver_ids, amounts, timestamps = generate_transactions(accounts_df)


    print(f"Generated {n_transactions.sum():,} transactions")
    print(f"Mean per account: {n_transactions.mean():.1f}")


    assert len(receiver_ids) == len(sender_ids)
    assert (sender_ids != receiver_ids).all()

    print(f"Sample timestamps (first 5): {list(timestamps[:5])}")
    print(f"Time range: {timestamps.min()} to {timestamps.max()}")

    hour_counts = pd.Series(timestamps).dt.hour.value_counts().sort_index()
    print(f"\nHour distribution:\n{hour_counts}")

    dow_counts = pd.Series(timestamps).dt.dayofweek.value_counts().sort_index()
    print(f"\nDay-of-week counts (Mon=0):\n{dow_counts}")

    day_counts = pd.Series(timestamps).dt.day.value_counts().sort_index()
    print(f"\nDay-of-month counts (spikes at 15 + last day):\n{day_counts}")



