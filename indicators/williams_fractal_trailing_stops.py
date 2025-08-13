import pandas as pd
import numpy as np

def williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0.5, flip_on="Close"):
    """
    Simplified Williams Fractal Trailing Stops function
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC data
        left_range (int): Left range for fractal calculation
        right_range (int): Right range for fractal calculation
        buffer_percent (float): Buffer percentage for trailing stops
        flip_on (str): Column to use for flip detection
        
    Returns:
        pd.DataFrame: DataFrame with fractal signals and trailing stops
    """
    n = len(df)
    df_out = pd.DataFrame(index=df.index)

    # Calculate the fractal highs: high is the max in window centered on current index with left_range and right_range
    is_williams_high = (df['high'] == df['high'].rolling(window=left_range + right_range + 1, center=True).max())

    # Calculate fractal lows: low is the min in the same window
    is_williams_low = (df['low'] == df['low'].rolling(window=left_range + right_range + 1, center=True).min())

    # Long and short stop plots (you can keep them as you had or customize)
    df_out['williams_long_stop_plot'] = df['close'].rolling(window=5, min_periods=1).min() * (1 - buffer_percent / 100)
    df_out['williams_short_stop_plot'] = df['close'].rolling(window=5, min_periods=1).max() * (1 + buffer_percent / 100)

    df_out['is_williams_high'] = is_williams_high
    df_out['is_williams_low'] = is_williams_low
    df_out['williams_high_price'] = df['high'].where(is_williams_high)
    df_out['williams_low_price'] = df['low'].where(is_williams_low)

    return df_out
