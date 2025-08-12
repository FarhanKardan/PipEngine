import pandas as pd
import numpy as np

def enhanced_zero_lag_macd(df, fast_length=12, slow_length=26, signal_length=9, 
                           macd_ema_length=9, use_ema=True, use_old_algo=False):
    """Calculate Enhanced Zero Lag MACD"""
    source = df['close']
    
    # Fast line (Zero Lag)
    if use_ema:
        ma1 = source.ewm(span=fast_length, adjust=False).mean()
        ma2 = ma1.ewm(span=fast_length, adjust=False).mean()
    else:
        ma1 = source.rolling(window=fast_length, min_periods=fast_length).mean()
        ma2 = ma1.rolling(window=fast_length, min_periods=fast_length).mean()
    zerolag_ema = (2 * ma1) - ma2
    
    # Slow line (Zero Lag)
    if use_ema:
        mas1 = source.ewm(span=slow_length, adjust=False).mean()
        mas2 = mas1.ewm(span=slow_length, adjust=False).mean()
    else:
        mas1 = source.rolling(window=slow_length, min_periods=slow_length).mean()
        mas2 = mas1.rolling(window=slow_length, min_periods=slow_length).mean()
    zerolag_slow_ma = (2 * mas1) - mas2
    
    # MACD line
    zero_lag_macd = zerolag_ema - zerolag_slow_ma
    
    # Signal line
    if use_old_algo:
        signal = zero_lag_macd.rolling(window=signal_length, min_periods=signal_length).mean()
    else:
        emasig1 = zero_lag_macd.ewm(span=signal_length, adjust=False).mean()
        emasig2 = emasig1.ewm(span=signal_length, adjust=False).mean()
        signal = (2 * emasig1) - emasig2
    
    # Histogram
    hist = zero_lag_macd - signal
    
    # Positive and negative histogram
    up_hist = np.where(hist > 0, hist, 0)
    down_hist = np.where(hist <= 0, hist, 0)
    
    # EMA on MACD line
    macd_ema = zero_lag_macd.ewm(span=macd_ema_length, adjust=False).mean()
    
    return pd.DataFrame({
        'zero_lag_macd': zero_lag_macd,
        'signal': signal,
        'histogram': hist,
        'up_histogram': up_hist,
        'down_histogram': down_hist,
        'macd_ema': macd_ema
    }, index=df.index)
