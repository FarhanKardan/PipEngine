import pandas as pd
import numpy as np

def calculate_true_range(df):
    """
    Calculate True Range (TR)
    
    Args:
        df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
    
    Returns:
        pd.Series: True Range values
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    # True Range is the maximum of the three
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    return true_range

def ma_function(source, length, smoothing="RMA"):
    """
    Moving average function with different smoothing options
    
    Args:
        source (pd.Series): Source data
        length (int): Period length
        smoothing (str): Smoothing type ("RMA", "SMA", "EMA", "WMA")
    
    Returns:
        pd.Series: Smoothed values
    """
    if smoothing == "RMA":
        # RMA (Relative Moving Average) - similar to EMA but with different multiplier
        multiplier = 1 / length
        rma = pd.Series(index=source.index, dtype=float)
        rma.iloc[length-1] = source.iloc[:length].mean()
        for i in range(length, len(source)):
            rma.iloc[i] = (source.iloc[i] * multiplier) + (rma.iloc[i-1] * (1 - multiplier))
        return rma
    elif smoothing == "SMA":
        return source.rolling(window=length, min_periods=length).mean()
    elif smoothing == "EMA":
        return source.ewm(span=length, adjust=False).mean()
    else:  # WMA
        weights = np.arange(1, length + 1)
        wma = source.rolling(window=length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
        return wma

def calculate_atr(df, length=14, smoothing="RMA"):
    """
    Calculate Average True Range (ATR) based on Pine Script implementation
    
    Args:
        df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
        length (int): Period for ATR calculation (default: 14)
        smoothing (str): Smoothing type ("RMA", "SMA", "EMA", "WMA") (default: "RMA")
    
    Returns:
        pd.Series: ATR values
    """
    # Calculate True Range
    true_range = calculate_true_range(df)
    
    # Apply smoothing using the specified method
    atr = ma_function(true_range, length, smoothing)
    
    return atr
