import pandas as pd
import numpy as np

def calculate_true_range(df):
    """Calculate True Range (TR)"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

def supertrend(df, atr_period=10, multiplier=3.0, change_atr_method=True, source='hl2'):
    """
    Calculate Supertrend indicator
    
    Args:
        df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
        atr_period (int): ATR period for calculation
        multiplier (float): ATR multiplier for band calculation
        change_atr_method (bool): True for ATR, False for SMA of TR
        source (str): Source price - 'hl2' for (high+low)/2, 'close' for close price
    
    Returns:
        pd.DataFrame: DataFrame with Supertrend components
    """
    # Calculate source price
    if source == 'hl2':
        src = (df['high'] + df['low']) / 2
    else:
        src = df['close']
    
    # Calculate ATR
    tr = calculate_true_range(df)
    if change_atr_method:
        atr = tr.ewm(span=atr_period, adjust=False).mean()
    else:
        atr = tr.rolling(window=atr_period, min_periods=atr_period).mean()
    
    # Calculate upper and lower bands
    up = src - (multiplier * atr)
    dn = src + (multiplier * atr)
    
    # Initialize arrays
    up_band = pd.Series(index=df.index, dtype=float)
    dn_band = pd.Series(index=df.index, dtype=float)
    trend = pd.Series(index=df.index, dtype=int)
    
    # Calculate Supertrend bands and trend
    for i in range(len(df)):
        if i == 0:
            up_band.iloc[i] = up.iloc[i]
            dn_band.iloc[i] = dn.iloc[i]
            trend.iloc[i] = 1
        else:
            # Upper band logic
            up1 = up_band.iloc[i-1] if not pd.isna(up_band.iloc[i-1]) else up.iloc[i]
            if df['close'].iloc[i-1] > up1:
                up_band.iloc[i] = max(up.iloc[i], up1)
            else:
                up_band.iloc[i] = up.iloc[i]
            
            # Lower band logic
            dn1 = dn_band.iloc[i-1] if not pd.isna(dn_band.iloc[i-1]) else dn.iloc[i]
            if df['close'].iloc[i-1] < dn1:
                dn_band.iloc[i] = min(dn.iloc[i], dn1)
            else:
                dn_band.iloc[i] = dn.iloc[i]
            
            # Trend logic
            prev_trend = trend.iloc[i-1] if not pd.isna(trend.iloc[i-1]) else 1
            if prev_trend == -1 and df['close'].iloc[i] > dn1:
                trend.iloc[i] = 1
            elif prev_trend == 1 and df['close'].iloc[i] < up1:
                trend.iloc[i] = -1
            else:
                trend.iloc[i] = prev_trend
    
    # Generate signals
    buy_signal = (trend == 1) & (trend.shift(1) == -1)
    sell_signal = (trend == -1) & (trend.shift(1) == 1)
    
    # Create plot series
    up_plot = np.where(trend == 1, up_band, np.nan)
    dn_plot = np.where(trend == -1, dn_band, np.nan)
    
    return pd.DataFrame({
        'trend': trend,
        'up_band': up_band,
        'dn_band': dn_band,
        'up_plot': up_plot,
        'dn_plot': dn_plot,
        'buy_signal': buy_signal,
        'sell_signal': sell_signal,
        'atr': atr
    }, index=df.index)
