import pandas as pd
import numpy as np
import mplfinance as mpf
import sys
import os

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

from datetime import datetime

# Add the project root to the path to import indicators
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import existing indicators
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

# Import config
from config import (
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_MAX_ROWS,
    EMA_PERIOD,
    WILLIAMS_FRACTAL_LEFT_RANGE,
    WILLIAMS_FRACTAL_RIGHT_RANGE
)

def load_and_prepare_data(path, symbol=None, start_date=None, end_date=None, max_rows=100):
    """
    Load and prepare data from CSV file with optional time range filtering
    
    Args:
        path (str): Path to CSV file
        symbol (str, optional): Symbol to filter by
        start_date (str, optional): Start date in 'YYYY-MM-DD' format
        end_date (str, optional): End date in 'YYYY-MM-DD' format
        max_rows (int, optional): Maximum number of rows to return (default: 100)
    """
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
    
    # Return first max_rows rows if specified, otherwise return all filtered data
    if max_rows and len(df) > max_rows:
        return df.iloc[:max_rows]  # Changed from df.iloc[-max_rows:] to df.iloc[:max_rows]
    else:
        return df

def add_ema(df, period=200, price_col='close'):
    """Add EMA to dataframe using existing indicator"""
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def calculate_strategy_positions(df, ema_col='ema_200'):
    """Calculate strategy positions based on EMA and Williams Fractal breakout logic"""
    long_positions = []
    short_positions = []
    long_entry_signals = []
    short_entry_signals = []
    
    # Track long positions
    has_long_position = False      # Whether we currently have an open long position
    long_entry_signal = False      # Flag for entering long at the *next* candle
    long_reference_high = None
    long_reference_low = None
    long_entry_candles = []        # Store long entry points
    
    # Track short positions
    has_short_position = False     # Whether we currently have an open short position
    short_entry_signal = False     # Flag for entering short at the *next* candle
    short_reference_low = None
    short_entry_candles = []       # Store short entry points

    for i in range(len(df)):
        open_i  = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        high_i  = df['high'].iloc[i]
        low_i   = df['low'].iloc[i]
        ema_i   = df[ema_col].iloc[i]
        ema200_i = df['ema_200'].iloc[i]

        current_long_pos = 1 if has_long_position else 0   # 1 if long position open, 0 if closed
        current_short_pos = -1 if has_short_position else 0  # -1 if short position open, 0 if closed
        current_long_entry_signal = 0
        current_short_entry_signal = 0

        # ---------------------------------------------------------
        # 1. Check for long position exit (EMA crossover)
        # ---------------------------------------------------------
        if has_long_position and close_i < ema_i:
            has_long_position = False
            current_long_pos = 0
            long_reference_high = None
            long_reference_low = None

        # ---------------------------------------------------------
        # 2. Check for short position exit (EMA crossover)
        # ---------------------------------------------------------
        if has_short_position and close_i > ema_i:
            has_short_position = False
            current_short_pos = 0
            short_reference_low = None

        # ---------------------------------------------------------
        # 3. Check for new long entry signals (only if no active long position)
        # ---------------------------------------------------------
        if not has_long_position and close_i > ema200_i:
            # Look for Williams fractal high above EMA
            if not pd.isna(df['williams_high_price'].iloc[i]) and low_i > ema_i:
                long_reference_high = df['high'].iloc[i]
                long_reference_low  = df['low'].iloc[i]

            # Check for breakout: 50% of body above reference_high
            if long_reference_high is not None:
                body = abs(close_i - open_i)
                if body > 0:
                    top = max(open_i, close_i)
                    bot = min(open_i, close_i)

                    if top <= long_reference_high:
                        body_above = 0
                    elif bot >= long_reference_high:
                        body_above = body
                    else:
                        body_above = top - long_reference_high

                    if body_above >= 0.5 * body:
                        long_entry_signal = True   # breakout detected

        # ---------------------------------------------------------
        # 4. Check for new short entry signals (only if no active short position)
        # ---------------------------------------------------------
        if not has_short_position and close_i < ema200_i:
            # Look for Williams fractal low below EMA
            if not pd.isna(df['williams_low_price'].iloc[i]) and high_i < ema_i:
                short_reference_low = df['low'].iloc[i]

            # Check for breakout: 50% of body below reference_low
            if short_reference_low is not None:
                body = abs(close_i - open_i)
                if body > 0:
                    top = max(open_i, close_i)
                    bot = min(open_i, close_i)

                    if bot >= short_reference_low:
                        body_below = 0
                    elif top <= short_reference_low:
                        body_below = body
                    else:
                        body_below = short_reference_low - bot

                    if body_below >= 0.5 * body:
                        short_entry_signal = True   # breakout detected

        # ---------------------------------------------------------
        # 5. Enter long position at the *next* candle
        # ---------------------------------------------------------
        if long_entry_signal and not has_long_position:
            has_long_position = True
            long_entry_candles.append(df.index[i])
            long_entry_signal = False
            current_long_pos = 1
            current_long_entry_signal = 1

        # ---------------------------------------------------------
        # 6. Enter short position at the *next* candle
        # ---------------------------------------------------------
        if short_entry_signal and not has_short_position:
            has_short_position = True
            short_entry_candles.append(df.index[i])
            short_entry_signal = False
            current_short_pos = -1
            current_short_entry_signal = 1

        # Combine positions (long takes precedence if both exist)
        if current_long_pos == 1:
            current_pos = 1
        elif current_short_pos == -1:
            current_pos = -1
        else:
            current_pos = 0

        long_positions.append(current_long_pos)
        short_positions.append(current_short_pos)
        long_entry_signals.append(current_long_entry_signal)
        short_entry_signals.append(current_short_entry_signal)

    # Final check
    assert len(long_positions) == len(df), f"{len(long_positions)} vs {len(df)}"
    assert len(short_positions) == len(df), f"{len(short_positions)} vs {len(df)}"
    assert len(long_entry_signals) == len(df), f"{len(long_entry_signals)} vs {len(df)}"
    assert len(short_entry_signals) == len(df), f"{len(short_entry_signals)} vs {len(df)}"

    # Create the strategy position and entry signal series
    df['strategy_position'] = pd.Series([1 if p == 1 else (-1 if p == -1 else 0) for p in [l if l == 1 else s for l, s in zip(long_positions, short_positions)]], index=df.index).astype(int)
    df['long_entry_signal'] = pd.Series(long_entry_signals, index=df.index).astype(int)
    df['short_entry_signal'] = pd.Series(short_entry_signals, index=df.index).astype(int)
    df['entry_signal'] = df['long_entry_signal'] + df['short_entry_signal']  # Combined entry signals
    
    return df

def create_plot(df, ema_col, symbol="XAUUSD"):
    """Create mplfinance plot with indicators and strategy positions"""
    
    # EMA as a line
    ema_plot = mpf.make_addplot(df[ema_col], color='blue')
    
    # Initialize addplots list with EMA
    addplots = [ema_plot]
    
    # Fractal plots - only add if columns exist and have data
    if 'williams_high_price' in df.columns and 'is_williams_high' in df.columns:
        high_fractals = df['williams_high_price'].copy()
        high_fractals = high_fractals.where(df['is_williams_high'], other=pd.NA)
        high_fractals = high_fractals.astype(float)
        
        # Only add if there are actual fractal points
        if not high_fractals.isna().all():
            high_fractal_plot = mpf.make_addplot(high_fractals, type='scatter', markersize=100, marker='v', color='red')
            addplots.append(high_fractal_plot)
    
    if 'williams_low_price' in df.columns and 'is_williams_low' in df.columns:
        low_fractals = df['williams_low_price'].copy()
        low_fractals = low_fractals.where(df['is_williams_low'], other=pd.NA)
        low_fractals = low_fractals.astype(float)
        
        # Only add if there are actual fractal points
        if not low_fractals.isna().all():
            low_fractal_plot = mpf.make_addplot(low_fractals, type='scatter', markersize=100, marker='^', color='green')
            addplots.append(low_fractal_plot)
    
    # Create entry markers - only show when positions actually increase
    position_changes = df['strategy_position'].diff().fillna(0)
    actual_entries = position_changes > 0  # Only when positions increase
    
    # Only add entry plots if there are actual entries
    if actual_entries.any():
        entry_markers = pd.Series(np.nan, index=df.index)
        entry_markers[actual_entries] = df.loc[actual_entries, 'low'] * 0.995
        entry_plot = mpf.make_addplot(entry_markers, type='scatter', markersize=100, marker='^', color='lime')
        addplots.append(entry_plot)
    
    # Add position level line if there are positions (only show changes, not repeated values)
    if df['strategy_position'].max() > 0:
        # Create a series that only shows position changes
        position_changes = df['strategy_position'].diff().fillna(0)
        position_changes = position_changes.where(position_changes != 0, np.nan)
        
        if not position_changes.isna().all():
            position_plot = mpf.make_addplot(position_changes, color='orange', ylabel='Position Changes', panel=1)
            addplots.append(position_plot)

    # Plot with mplfinance candlestick style
    mpf.plot(
        df,
        type='candle',
        style='charles',
        addplot=addplots,
        title=f"{symbol} - EMA + Williams Fractal Strategy",
        ylabel='Price',
        volume=True,
        figsize=(14,7)
    )

def main():
    """Main function to run the strategy"""
    csv_path = "results/data/klines.csv"
    symbol = "OANDA:XAUUSD"
    
    # Time range parameters - use config defaults
    start_date = DEFAULT_START_DATE
    end_date = DEFAULT_END_DATE
    max_rows = DEFAULT_MAX_ROWS

    try:
        # Load and prepare data with time range filtering
        print(f"Loading data for {symbol}")
        if start_date:
            print(f"From: {start_date}")
        if end_date:
            print(f"To: {end_date}")
        print(f"Max rows: {max_rows}")
        
        df = load_and_prepare_data(csv_path, symbol=symbol, 
                                 start_date=start_date, end_date=end_date, max_rows=max_rows)
        
        if df is None or df.empty:
            print("No data loaded")
            return

        print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Date range: {df.index.min()} to {df.index.max()}")

        # Add EMA using config period
        df, ema_col = add_ema(df, period=EMA_PERIOD, price_col='close')

        # Calculate Williams Fractal Trailing Stops using config ranges
        wft_df = williams_fractal_trailing_stops(
            df, 
            left_range=WILLIAMS_FRACTAL_LEFT_RANGE, 
            right_range=WILLIAMS_FRACTAL_RIGHT_RANGE, 
            buffer_percent=0, 
            flip_on="Close"
        )
        df = df.join(wft_df)

        # Calculate strategy positions
        df = calculate_strategy_positions(df, ema_col)
        
        # Show strategy summary
        total_positions = df['strategy_position'].max() if df['strategy_position'].max() > 0 else 0
        entry_signals = df['entry_signal'].sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        print(f"Strategy Summary: {total_positions} max positions, {entry_signals} entry signals, {neutral_positions} neutral")
        
        # Create plot
        create_plot(df, ema_col, symbol)
        
        # Save data to CSV for reference
        output_filename = f"strategy_1_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_filename)
        print(f"Data saved to: {output_filename}")
        
    except FileNotFoundError:
        print(f"File not found: {csv_path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
