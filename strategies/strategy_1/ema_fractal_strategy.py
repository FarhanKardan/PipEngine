import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

# Add the project root to the path to import indicators
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import existing indicators
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

def load_and_prepare_data(path, symbol=None):
    """Load and prepare data from CSV file"""
    df = pd.read_csv(path, parse_dates=['datetime'])
    if symbol:
        df = df[df['symbol'] == symbol].copy()
    df.set_index('datetime', inplace=True)
    df.columns = df.columns.str.lower()
    return df.iloc[-100:]  # last 100 rows

def add_ema(df, period=200, price_col='close'):
    """Add EMA to dataframe using existing indicator"""
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def calculate_strategy_positions(df, ema_col='ema_200'):
    """Calculate strategy positions based on EMA and Williams Fractal logic"""
    long_positions = []
    short_positions = []
    
    # Long position tracking
    long_position_open = False
    long_target_price = None
    long_pending_entry = False
    
    # Short position tracking
    short_position_open = False
    short_target_price = None
    short_pending_entry = False

    for i in range(len(df)):
        open_i  = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        ema_i   = df[ema_col].iloc[i]
        ema200_i = df[ema_col].iloc[i]

        current_long_pos = 0
        current_short_pos = 0

        # === LONG POSITION LOGIC ===
        # Invalidate target price if a low fractal appears
        if 'williams_low_price' in df.columns and not pd.isna(df['williams_low_price'].iloc[i]):
            long_target_price = None
            long_pending_entry = False

        # Update reference price if high fractal appears AND price above EMA
        if not pd.isna(df['williams_high_price'].iloc[i]) and close_i > ema_i:
            long_target_price = float(df['high'].iloc[i])
            long_pending_entry = False

        # Enter long on this candle if a pending entry was flagged
        if not long_position_open and long_pending_entry:
            long_position_open = True
            long_pending_entry = False
            current_long_pos = 1

        # Entry logic: check if at least 50% of body is above reference AND price above EMA200
        elif not long_position_open and long_target_price is not None and close_i > ema_i and close_i > ema200_i:
            body = abs(close_i - open_i)
            if body > 0:
                top = max(open_i, close_i)
                bot = min(open_i, close_i)

                if top <= long_target_price:
                    body_above = 0
                elif bot >= long_target_price:
                    body_above = body
                else:
                    body_above = top - long_target_price

                if body_above >= 0.5 * body:
                    long_pending_entry = True

        # Exit long logic
        elif long_position_open and close_i < ema_i:
            long_position_open = False
            current_long_pos = 0
        elif long_position_open:
            current_long_pos = 1

        # === SHORT POSITION LOGIC ===
        # Invalidate target price if ANY fractal appears between
        if (
            ('williams_high_price' in df.columns and not pd.isna(df['williams_high_price'].iloc[i])) or
            ('williams_low_price' in df.columns and not pd.isna(df['williams_low_price'].iloc[i]) and short_target_price is not None)
        ):
            short_target_price = None
            short_pending_entry = False

        # Update reference price only if low fractal appears AND price below EMA
        if not pd.isna(df['williams_low_price'].iloc[i]) and close_i < ema_i:
            short_target_price = float(df['low'].iloc[i])
            short_pending_entry = False

        # Enter short on this candle if a pending entry was flagged
        if not short_position_open and short_pending_entry:
            short_position_open = True
            short_pending_entry = False
            current_short_pos = -1

        # Entry logic: 50% body below target & below EMA200
        elif not short_position_open and short_target_price is not None and close_i < ema_i and close_i < ema200_i:
            body = abs(close_i - open_i)
            if body > 0:
                top = max(open_i, close_i)
                bot = min(open_i, close_i)

                if bot >= short_target_price:
                    body_below = 0
                elif top <= short_target_price:
                    body_below = body
                else:
                    body_below = short_target_price - bot

                if body_below >= 0.5 * body:
                    short_pending_entry = True

        # Exit short when price crosses above EMA
        elif short_position_open and close_i > ema_i:
            short_position_open = False
            current_short_pos = 0
        elif short_position_open:
            current_short_pos = -1

        long_positions.append(current_long_pos)
        short_positions.append(current_short_pos)

    # Combine long and short positions (long takes precedence if both exist)
    combined_positions = []
    for long_pos, short_pos in zip(long_positions, short_positions):
        if long_pos == 1:
            combined_positions.append(1)  # Long position
        elif short_pos == -1:
            combined_positions.append(-1)  # Short position
        else:
            combined_positions.append(0)   # Neutral

    return pd.Series(combined_positions, index=df.index).astype(int)

def main():
    """Main function to run the strategy"""
    csv_path = "klines.csv"
    symbol = "OANDA:XAUUSD"

    try:
        # Load and prepare data
        df = load_and_prepare_data(csv_path, symbol=symbol)
        
        if df is None or df.empty:
            print("No data loaded")
            return

        print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")

        # Add EMA
        df, ema_col = add_ema(df, period=200, price_col='close')

        # Calculate Williams Fractal Trailing Stops
        wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
        df = df.join(wft_df)

        # Calculate strategy positions
        df['strategy_position'] = calculate_strategy_positions(df, ema_col)
        
        # Show basic results
        long_positions = (df['strategy_position'] == 1).sum()
        short_positions = (df['strategy_position'] == -1).sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        print(f"Strategy Summary: {long_positions} long, {short_positions} short, {neutral_positions} neutral")
        
        print("Strategy execution completed successfully!")
        
    except FileNotFoundError:
        print(f"File not found: {csv_path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
