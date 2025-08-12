import pandas as pd
import numpy as np

def parabolic_sar(df, start=0.02, increment=0.02, maximum=0.2):
    """
    Calculate Parabolic SAR (Stop and Reverse)
    
    Args:
        df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
        start (float): Starting acceleration factor
        increment (float): Acceleration factor increment
        maximum (float): Maximum acceleration factor
    
    Returns:
        pd.Series: Parabolic SAR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Initialize arrays
    sar = pd.Series(index=df.index, dtype=float)
    af = pd.Series(index=df.index, dtype=float)
    ep = pd.Series(index=df.index, dtype=float)
    trend = pd.Series(index=df.index, dtype=int)
    
    # Initialize first values
    sar.iloc[0] = low.iloc[0]
    af.iloc[0] = start
    ep.iloc[0] = high.iloc[0]
    trend.iloc[0] = 1  # 1 for uptrend, -1 for downtrend
    
    # Calculate Parabolic SAR
    for i in range(1, len(df)):
        prev_sar = sar.iloc[i-1]
        prev_af = af.iloc[i-1]
        prev_ep = ep.iloc[i-1]
        prev_trend = trend.iloc[i-1]
        
        if prev_trend == 1:  # Uptrend
            # Check if trend continues
            if high.iloc[i] > prev_ep:
                # New high, update extreme point and acceleration factor
                ep.iloc[i] = high.iloc[i]
                af.iloc[i] = min(prev_af + increment, maximum)
            else:
                ep.iloc[i] = prev_ep
                af.iloc[i] = prev_af
            
            # Calculate SAR
            sar.iloc[i] = prev_sar + prev_af * (prev_ep - prev_sar)
            
            # Check if SAR is above low (trend reversal)
            if sar.iloc[i] > low.iloc[i]:
                # Trend reversal to downtrend
                trend.iloc[i] = -1
                sar.iloc[i] = prev_ep
                af.iloc[i] = start
                ep.iloc[i] = low.iloc[i]
            else:
                trend.iloc[i] = 1
                # Ensure SAR doesn't go above previous low
                if i > 1:
                    sar.iloc[i] = min(sar.iloc[i], low.iloc[i-1])
        
        else:  # Downtrend
            # Check if trend continues
            if low.iloc[i] < prev_ep:
                # New low, update extreme point and acceleration factor
                ep.iloc[i] = low.iloc[i]
                af.iloc[i] = min(prev_af + increment, maximum)
            else:
                ep.iloc[i] = prev_ep
                af.iloc[i] = prev_af
            
            # Calculate SAR
            sar.iloc[i] = prev_sar + prev_af * (prev_ep - prev_sar)
            
            # Check if SAR is below high (trend reversal)
            if sar.iloc[i] < high.iloc[i]:
                # Trend reversal to uptrend
                trend.iloc[i] = 1
                sar.iloc[i] = prev_ep
                af.iloc[i] = start
                ep.iloc[i] = high.iloc[i]
            else:
                trend.iloc[i] = -1
                # Ensure SAR doesn't go below previous high
                if i > 1:
                    sar.iloc[i] = max(sar.iloc[i], high.iloc[i-1])
    
    return sar
