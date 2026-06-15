from pathlib import Path
import pandas as pd

path = Path(__file__).parent / 'data' / 'institutions.csv'

institutions = pd.read_csv(path, dtype={'bank_code': str, 'weight': float})