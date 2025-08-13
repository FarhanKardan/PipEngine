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
    """Load and prepare data from CSV file"""
    df = pd.read_csv(path, parse_dates=['datetime'])
    if symbol:
        df = df[df['symbol'] == symbol].copy()
    df.set_index('datetime', inplace=True)
    df.columns = df.columns.str.lower()

    # Select last 100 candles properly indexed from -99 to end
    df = df.iloc[-100:]  # last 100 rows

    return df

def add_ema(df, period=200, price_col='close'):
    """Add EMA to dataframe using existing indicator"""
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def calculate_strategy_positions(df, ema_col='ema_200'):
    """
    Calculate strategy positions based on EMA and Williams Fractal logic
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC, EMA, and fractal data
        ema_col (str): Column name for EMA
        
    Returns:
        pd.Series: Strategy positions (1 for long, 0 for neutral)
    """
    positions = []
    position_open = False
    target_price = None
    pending_entry = False

    for i in range(len(df)):
        open_i  = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        high_i  = df['high'].iloc[i]
        ema_i   = df[ema_col].iloc[i]
        ema200_i = df['ema_200'].iloc[i]  # EMA200 column

        current_pos = 0  # default for this candle

        # Invalidate target price if a low fractal appears
        if 'williams_low_price' in df.columns and not pd.isna(df['williams_low_price'].iloc[i]):
            target_price = None
            pending_entry = False

        # Update reference price only if high fractal appears AND price above EMA AND no low fractal since
        if not pd.isna(df['williams_high_price'].iloc[i]) and close_i > ema_i:
            target_price = float(df['high'].iloc[i])
            pending_entry = False

        # Enter on this candle if a pending entry was flagged
        if not position_open and pending_entry:
            position_open = True
            pending_entry = False
            current_pos = 1

        # Entry logic: check if at least 50% of body is above reference AND price above EMA200
        elif not position_open and target_price is not None and close_i > ema_i and close_i > ema200_i:
            body = abs(close_i - open_i)
            if body > 0:
                top = max(open_i, close_i)
                bot = min(open_i, close_i)

                if top <= target_price:
                    body_above = 0
                elif bot >= target_price:
                    body_above = body
                else:
                    body_above = top - target_price

                if body_above >= 0.5 * body:
                    pending_entry = True

        # Exit logic
        elif position_open and close_i < ema_i:
            position_open = False
            current_pos = 0
        elif position_open:
            current_pos = 1

        positions.append(current_pos)

    # Final check
    assert len(positions) == len(df), f"{len(positions)} vs {len(df)}"

    return pd.Series(positions, index=df.index).astype(int)

def create_plot(df, ema_col, symbol="XAUUSD"):
    """Create mplfinance plot with indicators and strategy positions"""
    
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

    # Create entry/exit markers based on strategy positions
    entry_signal = (df['strategy_position'] == 1) & (df['strategy_position'].shift(1) != 1)
    exit_signal = (df['strategy_position'] == 0) & (df['strategy_position'].shift(1) == 1)
    
    # Create marker series for entry and exit signals
    entry_markers = pd.Series(np.nan, index=df.index)
    exit_markers = pd.Series(np.nan, index=df.index)
    
    entry_markers[entry_signal] = df.loc[entry_signal, 'low'] * 0.995
    exit_markers[exit_signal] = df.loc[exit_signal, 'high'] * 1.005
    
    # Create addplots for entry and exit signals
    entry_plot = mpf.make_addplot(entry_markers, type='scatter', markersize=100, marker='^', color='lime')
    exit_plot = mpf.make_addplot(exit_markers, type='scatter', markersize=100, marker='v', color='orange')

    # Compose all addplots
    addplots = [ema_plot, high_fractal_plot, low_fractal_plot, entry_plot, exit_plot]

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
    
    # === Main ===
    csv_path = "klines.csv"
    symbol = "OANDA:XAUUSD"

    print("🚀 Starting EMA + Williams Fractal Strategy")
    print("=" * 50)

    try:
        # Load and prepare data
        print("📊 Loading data...")
        df = load_and_prepare_data(csv_path, symbol=symbol)
        
        if df is None or df.empty:
            print("❌ No data loaded")
            return
        
        print(f"📈 Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")

        # Add EMA
        print("📊 Adding EMA indicator...")
        df, ema_col = add_ema(df, period=200, price_col='close')

        # Calculate Williams Fractal Trailing Stops
        print("🧮 Calculating Williams Fractal Trailing Stops...")
        wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
        df = df.join(wft_df)

        # Calculate strategy positions
        print("📊 Calculating strategy positions...")
        df['strategy_position'] = calculate_strategy_positions(df, ema_col)
        
        # Show strategy summary
        long_positions = (df['strategy_position'] == 1).sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        print(f"📊 Strategy Summary:")
        print(f"   Long positions: {long_positions}")
        print(f"   Neutral positions: {neutral_positions}")
        
        # Create plot
        print("📈 Creating plot...")
        create_plot(df, ema_col, symbol)
        
        # Save data to CSV for reference
        output_filename = f"strategy_1_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_filename)
        print(f"💾 Data saved to: {output_filename}")
        
        print("✅ Strategy execution completed successfully!")
        
    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
