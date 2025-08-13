import pandas as pd
import numpy as np
import mplfinance as mpf
import sys
import os

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

from datetime import datetime

# Add the project root to the path to import indicators
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import existing indicators
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

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
    
    # Return last max_rows rows if specified, otherwise return all filtered data
    if max_rows and len(df) > max_rows:
        return df.iloc[-max_rows:]
    else:
        return df

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
        ema200_i = df['ema_200'].iloc[i]

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
    
    # Create entry/exit markers based on strategy positions
    entry_signal = (df['strategy_position'] == 1) & (df['strategy_position'].shift(1) != 1)
    exit_signal = (df['strategy_position'] == 0) & (df['strategy_position'].shift(1) == 1)
    
    # Only add entry/exit plots if there are actual signals
    if entry_signal.any():
        entry_markers = pd.Series(np.nan, index=df.index)
        entry_markers[entry_signal] = df.loc[entry_signal, 'low'] * 0.995
        entry_plot = mpf.make_addplot(entry_markers, type='scatter', markersize=100, marker='^', color='lime')
        addplots.append(entry_plot)
    
    if exit_signal.any():
        exit_markers = pd.Series(np.nan, index=df.index)
        exit_markers[exit_signal] = df.loc[exit_signal, 'high'] * 1.005
        exit_plot = mpf.make_addplot(exit_markers, type='scatter', markersize=100, marker='v', color='orange')
        addplots.append(exit_plot)

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
    csv_path = "klines.csv"
    symbol = "OANDA:XAUUSD"
    
    # Time range parameters - customize these as needed
    start_date = None  # "2024-01-01"  # Start date in YYYY-MM-DD format
    end_date = None    # "2024-12-31"  # End date in YYYY-MM-DD format
    max_rows = 100     # Maximum number of rows to analyze

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

        # Add EMA
        df, ema_col = add_ema(df, period=200, price_col='close')

        # Calculate Williams Fractal Trailing Stops
        wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
        df = df.join(wft_df)

        # Calculate strategy positions
        df['strategy_position'] = calculate_strategy_positions(df, ema_col)
        
        # Show strategy summary
        long_positions = (df['strategy_position'] == 1).sum()
        short_positions = (df['strategy_position'] == -1).sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        print(f"Strategy Summary: {long_positions} long, {short_positions} short, {neutral_positions} neutral")
        
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
