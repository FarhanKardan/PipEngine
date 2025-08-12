import pandas as pd
import numpy as np

def calc_smma(src, length):
    """Calculate Smoothed Moving Average (SMMA)"""
    smma = src.ewm(span=length, adjust=False).mean()
    return smma

def calc_zlema(src, length):
    """Calculate Zero Lag Exponential Moving Average (ZLEMA)"""
    ema1 = src.ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    return ema1 + (ema1 - ema2)

def impulse_macd_lb(df, length_ma=34, length_signal=9):
    """Calculate Impulse MACD"""
    src = (df['high'] + df['low'] + df['close']) / 3
    hi = calc_smma(df['high'], length_ma)
    lo = calc_smma(df['low'], length_ma)
    mi = calc_zlema(src, length_ma)

    md = pd.Series(0.0, index=df.index)
    for i in range(len(df)):
        if not (np.isnan(mi.iloc[i]) or np.isnan(hi.iloc[i]) or np.isnan(lo.iloc[i])):
            if mi.iloc[i] > hi.iloc[i]:
                md.iloc[i] = mi.iloc[i] - hi.iloc[i]
            elif mi.iloc[i] < lo.iloc[i]:
                md.iloc[i] = mi.iloc[i] - lo.iloc[i]

    sb = md.rolling(window=length_signal, min_periods=1).mean()
    sh = md - sb

    mdc = []
    for i in range(len(df)):
        if not (np.isnan(md.iloc[i]) or np.isnan(mi.iloc[i]) or np.isnan(hi.iloc[i]) or np.isnan(lo.iloc[i]) or np.isnan(src.iloc[i])):
            if src.iloc[i] > mi.iloc[i]:
                if src.iloc[i] > hi.iloc[i]:
                    mdc.append('lime')
                else:
                    mdc.append('green')
            else:
                if src.iloc[i] < lo.iloc[i]:
                    mdc.append('red')
                else:
                    mdc.append('orange')
        else:
            mdc.append(None)

    return pd.DataFrame({'md': md, 'sb': sb, 'sh': sh, 'mdc': mdc}, index=df.index)
