import pandas as pd
from .ema import calculate_ema

def calculate_dema(data, period=9):
    """Calculate Double Exponential Moving Average"""
    e1 = calculate_ema(data, period)
    e2 = calculate_ema(e1, period)
    return 2 * e1 - e2

