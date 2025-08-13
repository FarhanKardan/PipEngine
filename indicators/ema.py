import pandas as pd
import numpy as np

def calculate_ema(price_series, period):
    """
    Calculate Exponential Moving Average
    
    Args:
        price_series (pd.Series): Price series (close, open, high, low)
        period (int): Period for EMA calculation
        
    Returns:
        pd.Series: EMA values
    """
    return price_series.ewm(span=period, adjust=False).mean()


