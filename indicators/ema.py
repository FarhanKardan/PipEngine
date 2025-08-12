import pandas as pd
import numpy as np

def calculate_ema(data, period=9, offset=0):
    if not isinstance(data, pd.Series):
        raise ValueError("Data must be a pandas Series")
    
    if period <= 0:
        raise ValueError("Period must be greater than 0")
    
    if len(data) < period:
        raise ValueError(f"Data length ({len(data)}) must be at least period ({period})")
    
    multiplier = 2 / (period + 1)
    
    ema = pd.Series(index=data.index, dtype=float)
    ema.iloc[period-1] = data.iloc[:period].mean()
    
    for i in range(period, len(data)):
        ema.iloc[i] = (data.iloc[i] * multiplier) + (ema.iloc[i-1] * (1 - multiplier))
    
    if offset != 0:
        ema = ema.shift(offset)
    
    return ema


