import pandas as pd
import numpy as np

def calculate_true_range(df):
    """Calculate True Range (TR)"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

def calculate_atr(df, length=14, smoothing="RMA"):
    """Calculate Average True Range (ATR)"""
    true_range = calculate_true_range(df)
    
    if smoothing == "RMA":
        # RMA (Relative Moving Average) - similar to EMA
        return true_range.ewm(span=length, adjust=False).mean()
    elif smoothing == "SMA":
        return true_range.rolling(window=length, min_periods=length).mean()
    elif smoothing == "EMA":
        return true_range.ewm(span=length, adjust=False).mean()
    else:  # WMA
        weights = np.arange(1, length + 1)
        return true_range.rolling(window=length).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
