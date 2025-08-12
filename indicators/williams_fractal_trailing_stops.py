import pandas as pd
import numpy as np

def williams_fractal_trailing_stops(df, left_range=2, right_range=2, buffer_percent=0, flip_on="Close"):
    """
    Calculate Williams Fractal Trailing Stops
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Check if current bar confirms a Williams High or Low
    def is_williams_fractal(high_data, low_data, left_range, right_range, fractal_type):
        if fractal_type == "high":
            # Check if high[right_range] is the highest in the range
            window_size = left_range + right_range + 1
            highest_in_range = high_data.rolling(window=window_size, min_periods=window_size).max()
            return high_data.shift(right_range) >= highest_in_range.shift(right_range)
        else:  # low
            # Check if low[right_range] is the lowest in the range
            window_size = left_range + right_range + 1
            lowest_in_range = low_data.rolling(window=window_size, min_periods=window_size).min()
            return low_data.shift(right_range) <= lowest_in_range.shift(right_range)
    
    # Calculate Williams fractals
    is_williams_high = is_williams_fractal(high, low, left_range, right_range, "high")
    is_williams_low = is_williams_fractal(high, low, left_range, right_range, "low")
    
    # Suppress fractals if the previous bar was a fractal
    is_williams_high = is_williams_high & ~is_williams_high.shift(1)
    is_williams_low = is_williams_low & ~is_williams_low.shift(1)
    
    # Get fractal prices
    williams_high_price = np.where(is_williams_high, high.shift(right_range), np.nan)
    williams_low_price = np.where(is_williams_low, low.shift(right_range), np.nan)
    
    # Add buffer
    williams_high_price_buffered = williams_high_price * (1 + (buffer_percent / 100))
    williams_low_price_buffered = williams_low_price * (1 - (buffer_percent / 100))
    
    # Initialize trailing stops
    williams_long_stop_price = pd.Series(index=df.index, dtype=float)
    williams_short_stop_price = pd.Series(index=df.index, dtype=float)
    
    # Persist and reset trailing stops
    for i in range(len(df)):
        if i == 0:
            williams_long_stop_price.iloc[i] = williams_low_price_buffered.iloc[i] if not np.isnan(williams_low_price_buffered.iloc[i]) else np.nan
            williams_short_stop_price.iloc[i] = williams_high_price_buffered.iloc[i] if not np.isnan(williams_high_price_buffered.iloc[i]) else np.nan
        else:
            if not np.isnan(williams_low_price_buffered.iloc[i]):
                williams_long_stop_price.iloc[i] = williams_low_price_buffered.iloc[i]
            else:
                williams_long_stop_price.iloc[i] = williams_long_stop_price.iloc[i-1]
            
            if not np.isnan(williams_high_price_buffered.iloc[i]):
                williams_short_stop_price.iloc[i] = williams_high_price_buffered.iloc[i]
            else:
                williams_short_stop_price.iloc[i] = williams_short_stop_price.iloc[i-1]
    
    # Trail the stops
    williams_long_stop_price_trail = williams_long_stop_price.copy()
    williams_short_stop_price_trail = williams_short_stop_price.copy()
    
    for i in range(1, len(df)):
        # Trail long stop up
        if close.iloc[i] >= williams_long_stop_price_trail.iloc[i-1]:
            williams_long_stop_price_trail.iloc[i] = williams_long_stop_price_trail.iloc[i-1]
        
        # Trail short stop down
        if close.iloc[i] <= williams_short_stop_price_trail.iloc[i-1]:
            williams_short_stop_price_trail.iloc[i] = williams_short_stop_price_trail.iloc[i-1]
    
    # Determine flip conditions
    flip_source = close if flip_on == "Close" else high if flip_on == "Wick" else close
    
    # Initialize state variables
    is_long = pd.Series(True, index=df.index)
    is_short = pd.Series(True, index=df.index)
    
    # Calculate flip logic
    for i in range(1, len(df)):
        # Check for flips
        flip_long = is_short.iloc[i-1] and flip_source.iloc[i] > williams_short_stop_price_trail.iloc[i-1]
        flip_short = is_long.iloc[i-1] and flip_source.iloc[i] < williams_long_stop_price_trail.iloc[i-1]
        
        # Handle edge cases
        if flip_long and flip_short:
            if close.iloc[i] > williams_long_stop_price_trail.iloc[i]:
                flip_short = False
            else:
                flip_long = False
        
        # Update state
        if flip_long:
            is_long.iloc[i] = True
            is_short.iloc[i] = False
        elif flip_short:
            is_long.iloc[i] = False
            is_short.iloc[i] = True
        else:
            is_long.iloc[i] = is_long.iloc[i-1]
            is_short.iloc[i] = is_short.iloc[i-1]
    
    # Create plot series (hide when not active)
    williams_long_stop_plot = np.where(is_long, williams_long_stop_price_trail, np.nan)
    williams_short_stop_plot = np.where(is_short, williams_short_stop_price_trail, np.nan)
    
    return pd.DataFrame({
        'is_williams_high': is_williams_high,
        'is_williams_low': is_williams_low,
        'williams_high_price': williams_high_price,
        'williams_low_price': williams_low_price,
        'williams_long_stop': williams_long_stop_price_trail,
        'williams_short_stop': williams_short_stop_price_trail,
        'williams_long_stop_plot': williams_long_stop_plot,
        'williams_short_stop_plot': williams_short_stop_plot,
        'is_long': is_long,
        'is_short': is_short
    }, index=df.index)
