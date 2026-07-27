import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from config import SIMULATION_START, SIMULATION_END, DEFAULT_SEED
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

if __name__ == '__main__':

    rng = np.random.default_rng(DEFAULT_SEED)
    accounts_df = generate_accounts(10_000)
    mule_pools = select_mule_accounts(accounts_df, rng)

    for typology, pool in mule_pools.items():
        print(f"{typology}: {len(pool)} mules")

    rng = np.random.default_rng(DEFAULT_SEED)

