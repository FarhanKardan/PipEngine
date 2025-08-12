import pandas as pd

def calculate_ema(data, period=9, offset=0):
    """Calculate Exponential Moving Average"""
    ema = data.ewm(span=period, adjust=False).mean()
    if offset != 0:
        ema = ema.shift(offset)
    return ema


