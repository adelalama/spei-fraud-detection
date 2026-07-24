import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from config import SIMULATION_START, SIMULATION_END, DEFAULT_SEED
from transactions import AMOUNT_REGIMES
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

if __name__ == '__main__':

    rng = np.random.default_rng(DEFAULT_SEED)
    accounts_df = generate_accounts(10_000)
    mule_pools = select_mule_accounts(accounts_df, rng)

    for typology, pool in mule_pools.items():
        print(f"{typology}: {len(pool)} mules")