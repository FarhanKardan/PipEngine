import pandas as pd
import numpy as np
import mplfinance as mpf
import sys
import os

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

from datetime import datetime, timedelta

# Add the project root to the path to import indicators
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import existing indicators
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

def load_and_prepare_data(path, symbol=None):
    df = pd.read_csv(path, parse_dates=['datetime'])
    if symbol:
        df = df[df['symbol'] == symbol].copy()
    df.set_index('datetime', inplace=True)
    df.columns = df.columns.str.lower()

    # Select last 100 candles properly indexed from -99 to end
    df = df.iloc[-100:]  # last 100 rows

    return df

# Add EMA using existing indicator
def add_ema(df, period=200, price_col='close'):
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def main():
    # === Main ===
    csv_path = "klines.csv"
    symbol = "OANDA:XAUUSD"

    df = load_and_prepare_data(csv_path, symbol=symbol)

    df, ema_col = add_ema(df, period=200, price_col='close')

    wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
    df = df.join(wft_df)

    # Prepare additional plots for mplfinance

    # EMA as a line
    ema_plot = mpf.make_addplot(df[ema_col], color='blue')

    # Trailing stops as lines
    long_stop_plot = mpf.make_addplot(df['williams_long_stop_plot'], color='green')
    short_stop_plot = mpf.make_addplot(df['williams_short_stop_plot'], color='red')

    # Scatter plots for fractals
    # mplfinance does not natively support scatter plots, but we can mark fractals as points on a separate panel or overlay

    # For fractals, create "marker" series with NaN except fractal points
    high_fractals = df['williams_high_price'].copy()
    low_fractals = df['williams_low_price'].copy()

    # Replace NaNs with None to avoid plotting issues
    high_fractals = high_fractals.where(df['is_williams_high'], other=pd.NA)
    low_fractals = low_fractals.where(df['is_williams_low'], other=pd.NA)

    # mplfinance expects numeric with NaN, so convert pd.NA back to np.nan
    high_fractals = high_fractals.astype(float)
    low_fractals = low_fractals.astype(float)

    # Create addplots for fractal markers, use scatter marker style
    high_fractal_plot = mpf.make_addplot(high_fractals, type='scatter', markersize=100, marker='v', color='red')
    low_fractal_plot = mpf.make_addplot(low_fractals, type='scatter', markersize=100, marker='^', color='green')

    # Compose all addplots
    addplots = [ema_plot, high_fractal_plot, low_fractal_plot]

    # Plot with mplfinance candlestick style
    mpf.plot(
        df,
        type='candle',
        style='charles',
        addplot=addplots,
        title=f"{symbol} - EMA + Williams Fractal Markers",
        ylabel='Price',
        volume=True,
        figsize=(14,7)
    )

if __name__ == "__main__":
    main()
