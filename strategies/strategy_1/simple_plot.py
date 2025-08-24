import pandas as pd
import mplfinance as mpf

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

from datetime import datetime, timedelta
import numpy as np

def load_and_prepare_data(path, symbol=None, start_date=None, end_date=None, max_rows=100):
    df = pd.read_csv(path, parse_dates=['datetime'])

    # Filter by symbol if provided
    if symbol:
        df = df[df['symbol'] == symbol].copy()

    # Set datetime as index
    df.set_index('datetime', inplace=True)
    df.columns = df.columns.str.lower()

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df.index >= start_dt]

    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df.index <= end_dt]

    # Sort by datetime to ensure proper order
    df = df.sort_index()

    # Return last max_rows rows if specified, otherwise return all filtered data
    if max_rows and len(df) > max_rows:
        return df.iloc[-max_rows:]
    else:
        return df

# Add EMA
def add_ema(df, period=200, price_col='close'):
    ema_col = f'ema_{period}'
    df[ema_col] = df[price_col].ewm(span=period, adjust=False).mean()
    return df, ema_col

# Simplified Williams Fractal Trailing Stops function
def williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0.5, flip_on="Close"):
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

def calculate_strategy_positions(df, ema_col='ema_200'):
    """Calculate strategy positions based on EMA and Williams Fractal breakout logic"""
    positions = []
    open_positions = 0      # number of active positions
    entry_signal = False    # flag for entering at the *next* candle
    reference_high = None
    reference_low = None
    entry_candles = []      # store entry points

    for i in range(len(df)):
        open_i  = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        high_i  = df['high'].iloc[i]
        low_i   = df['low'].iloc[i]
        ema_i   = df[ema_col].iloc[i]
        ema200_i = df['ema_200'].iloc[i]

        current_pos = open_positions  # default = current open count

        # ---------------------------------------------------------
        # Invalidate reference if price crosses below EMA
        # ---------------------------------------------------------
        if close_i < ema_i:
            reference_high = None
            reference_low = None

        # ---------------------------------------------------------
        # 1. Only consider longs if close is above EMA200
        # ---------------------------------------------------------
        if close_i > ema200_i:

            # -----------------------------------------------------
            # 2. Roll back to last williams_high_price (must be above EMA)
            # -----------------------------------------------------
            if not pd.isna(df['williams_high_price'].iloc[i]) and low_i > ema_i:
                reference_high = df['high'].iloc[i]
                reference_low  = df['low'].iloc[i]

            # -----------------------------------------------------
            # 3. Breakout check: 50% of body above reference_high
            # -----------------------------------------------------
            if reference_high is not None:
                body = abs(close_i - open_i)
                if body > 0:
                    top = max(open_i, close_i)
                    bot = min(open_i, close_i)

                    if top <= reference_high:
                        body_above = 0
                    elif bot >= reference_high:
                        body_above = body
                    else:
                        body_above = top - reference_high

                    if body_above >= 0.5 * body:
                        entry_signal = True   # breakout detected

        # ---------------------------------------------------------
        # 4. Enter position at the next candle
        # ---------------------------------------------------------
        if entry_signal:
            open_positions += 1        # add new position
            entry_candles.append(df.index[i])  # log entry
            entry_signal = False
            current_pos = open_positions

        # Exit logic: close below EMA → close ALL open positions
        if open_positions > 0 and close_i < ema_i:
            open_positions = 0
            current_pos = 0

        positions.append(current_pos)

    # Final check
    assert len(positions) == len(df), f"{len(positions)} vs {len(df)}"

    # Create the strategy position series
    df['strategy_position'] = pd.Series(positions, index=df.index).astype(int)
    df['entry_signal'] = 0
    df.loc[entry_candles, 'entry_signal'] = 1
    
    return df

# === Main ===
csv_path = "klines.csv"
symbol = "OANDA:XAUUSD"

start_date = "2025-08-01"  # Start date in YYYY-MM-DD format
end_date = "2025-08-02"
df = load_and_prepare_data(csv_path, symbol=symbol,
                                 start_date=start_date, end_date=end_date, max_rows=500)

df, ema_col = add_ema(df, period=200, price_col='close')

wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
df = df.join(wft_df)

# Calculate strategy positions
df = calculate_strategy_positions(df, ema_col)

# Show strategy summary
total_positions = df['strategy_position'].max() if df['strategy_position'].max() > 0 else 0
entry_signals = df['entry_signal'].sum()
neutral_positions = (df['strategy_position'] == 0).sum()
print(f"Strategy Summary: {total_positions} max positions, {entry_signals} entry signals, {neutral_positions} neutral")

# Prepare additional plots for mplfinance

# EMA as a line
ema_plot = mpf.make_addplot(df[ema_col], color='blue')

# Strategy position line
position_plot = mpf.make_addplot(df['strategy_position'], color='orange', ylabel='Positions', panel=1)

# Entry signals
entry_markers = pd.Series(np.nan, index=df.index)
entry_markers[df['entry_signal'] == 1] = df.loc[df['entry_signal'] == 1, 'low'] * 0.995
entry_plot = mpf.make_addplot(entry_markers, type='scatter', markersize=100, marker='^', color='lime')

# Scatter plots for fractals
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
addplots = [ema_plot, entry_plot, high_fractal_plot, low_fractal_plot, position_plot]

# Plot with mplfinance candlestick style
mpf.plot(
    df,
    type='candle',
    style='charles',
    addplot=addplots,
    title=f"{symbol} - EMA + Williams Fractal Strategy",
    ylabel='Price',
    volume=True,
    figsize=(14,10)
)
