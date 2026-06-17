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

def generate_transactions(accounts_df, seed = DEFAULT_SEED):
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

    return (n_transactions, sender_ids, beneficiary_networks, receiver_ids)


#function to build network of recurring transactions for each account
def build_beneficiary_networks(accounts_df, rng):
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

        beneficiary_networks[account_id] = combined

    return beneficiary_networks

def sample_new_beneficiary(sender_id, sender_segment, existing_network, accounts_by_segment, all_account_ids, rng):
    #same segment
    if rng.random()<.7:
        candidates = accounts_by_segment[sender_segment]
    else:
        candidates = all_account_ids

    excluded = set(existing_network).union({sender_id})
    eligible =[i for i in candidates if i not in excluded]

    return rng.choice(eligible)

def assign_transaction_receiver(sender_ids, beneficiary_networks, accounts_df, rng):

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

    return np.array(receiver_ids)


if __name__ == "__main__":
    from src.data_generator.accounts import generate_accounts
    rng = np.random.default_rng(DEFAULT_SEED)

    accounts_df = generate_accounts(10_000)
    n_transactions, sender_ids, networks, receiver_ids = generate_transactions(accounts_df)

    print(f"Generated {n_transactions.sum():,} transactions")
    print(f"Mean per account: {n_transactions.mean():.1f}")


    assert len(receiver_ids) == len(sender_ids)
    assert (sender_ids != receiver_ids).all()
