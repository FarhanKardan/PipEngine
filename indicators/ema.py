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

def calculate_multiple_ema(data, periods=[9, 21, 50]):
    if not isinstance(data, pd.Series):
        raise ValueError("Data must be a pandas Series")
    
    ema_data = pd.DataFrame(index=data.index)
    
    for period in periods:
        if period > 0:
            ema_data[f'EMA_{period}'] = calculate_ema(data, period)
    
    return ema_data

def ema_crossover_signal(data, fast_period=9, slow_period=21):
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")
    
    fast_ema = calculate_ema(data, fast_period)
    slow_ema = calculate_ema(data, slow_period)
    
    signals = pd.Series(0, index=data.index)
    
    signals[(fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))] = 1
    
    signals[(fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))] = -1
    
    return signals

if __name__ == "__main__":
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
    
    print("Sample Data:")
    print(sample_data.head())
    print("\n" + "="*50)
    
    ema_9 = calculate_ema(sample_data, 9)
    print(f"EMA(9):")
    print(ema_9.head(25))
    print("\n" + "="*50)
    
    ema_9_offset = calculate_ema(sample_data, 9, offset=2)
    print(f"EMA(9) with offset 2:")
    print(ema_9_offset.head(25))
    print("\n" + "="*50)
    
    multiple_emas = calculate_multiple_ema(sample_data, [9, 21, 50])
    print("Multiple EMAs:")
    print(multiple_emas.head(25))
    print("\n" + "="*50)
    
    signals = ema_crossover_signal(sample_data, 9, 21)
    print("EMA Crossover Signals:")
    print(signals.value_counts())
