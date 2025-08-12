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

if __name__ == "__main__":
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    
    print("Sample Data:")
    print(sample_data.head())
    print("\n" + "="*50)
    
    dema_9 = calculate_dema(sample_data, 9)
    print(f"DEMA(9):")
    print(dema_9.head(25))
    print("\n" + "="*50)
    
    dema_21 = calculate_dema(sample_data, 21)
    print(f"DEMA(21):")
    print(dema_21.head(25))
