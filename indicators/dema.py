import pandas as pd
import numpy as np
from ema import calculate_ema

def calculate_dema(data, period=9):
    if not isinstance(data, pd.Series):
        raise ValueError("Data must be a pandas Series")
    
    if period <= 0:
        raise ValueError("Period must be greater than 0")
    
    if len(data) < period:
        raise ValueError(f"Data length ({len(data)}) must be at least period ({period})")
    
    e1 = calculate_ema(data, period)
    e2 = calculate_ema(e1, period)
    dema = 2 * e1 - e2
    
    return dema

