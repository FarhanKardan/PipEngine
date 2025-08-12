#!/usr/bin/env python3
"""
Plot Williams Fractal Trailing Stops indicator
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Add paths
sys.path.append('data feeder')
sys.path.append('indicators')

from data_feeder import DataFeeder
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops
from indicators.ema import calculate_ema

def plot_williams_fractal():
    """Plot Williams Fractal Trailing Stops indicator"""
    
    # Fetch data
    print("📊 Fetching XAUUSD data...")
    feeder = DataFeeder()
    df = feeder.fetch_xauusd(n_bars=100)
    
    if df is None or df.empty:
        print("❌ No data received")
        return
    
    print(f"✅ Fetched {len(df)} bars of XAUUSD data")
    
    # Calculate Williams Fractal
    print("🧮 Calculating Williams Fractal Trailing Stops...")
    result = williams_fractal_trailing_stops(df, 2, 2, 0, 'Close')
    
    # Calculate EMA 200
    print("📊 Calculating EMA 200...")
    ema_200 = calculate_ema(df['close'], 200)
    
    # Create the plot
    print("📈 Creating visualization...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    fig.suptitle('Williams Fractal Trailing Stops - XAUUSD', fontsize=16, fontweight='bold')
    
    # Plot 1: Price with Trailing Stops
    ax1.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1, alpha=0.7)
    ax1.plot(df.index, df['high'], label='High', color='gray', linewidth=0.5, alpha=0.5)
    ax1.plot(df.index, df['low'], label='Low', color='gray', linewidth=0.5, alpha=0.5)
    
    # Plot EMA 200
    ax1.plot(df.index, ema_200, label='EMA 200', color='purple', linewidth=2, alpha=0.8)
    
    # Plot trailing stops
    ax1.plot(result.index, result['williams_long_stop_plot'], 
             label='Long Stop (Uptrend)', color='green', linewidth=2)
    ax1.plot(result.index, result['williams_short_stop_plot'], 
             label='Short Stop (Downtrend)', color='red', linewidth=2)
    
    # Plot fractal points
    high_fractals = result[result['is_williams_high']]
    low_fractals = result[result['is_williams_low']]
    
    if not high_fractals.empty:
        ax1.scatter(high_fractals.index, high_fractals['williams_high_price'], 
                   color='red', marker='v', s=50, label='Williams High', alpha=0.8)
    
    if not low_fractals.empty:
        ax1.scatter(low_fractals.index, low_fractals['williams_low_price'], 
                   color='green', marker='^', s=50, label='Williams Low', alpha=0.8)
    
    ax1.set_title('Price with Williams Fractal Trailing Stops')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Position Status
    ax2.plot(result.index, result['is_long'].astype(int), label='Long Position', 
             color='green', linewidth=2)
    ax2.plot(result.index, -result['is_short'].astype(int), label='Short Position', 
             color='red', linewidth=2)
    
    # Plot position changes
    long_changes = result[result['is_long'] & ~result['is_long'].shift(1).fillna(False)]
    short_changes = result[result['is_short'] & ~result['is_short'].shift(1).fillna(False)]
    
    if not long_changes.empty:
        ax2.scatter(long_changes.index, [1] * len(long_changes), 
                   color='green', marker='^', s=100, label='Go Long', alpha=0.8)
    
    if not short_changes.empty:
        ax2.scatter(short_changes.index, [-1] * len(short_changes), 
                   color='red', marker='v', s=100, label='Go Short', alpha=0.8)
    
    ax2.set_title('Position Status (1=Long, -1=Short)')
    ax2.set_ylabel('Position')
    ax2.set_ylim(-1.5, 1.5)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis for both plots
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    import os
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"Williams_Fractal_Chart_{timestamp}.png"
    fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"🖼️ Chart saved to: {plot_filename}")
    
    # Show plot
    plt.show()
    
    # Print summary
    print(f"\n📊 Williams Fractal Summary:")
    print(f"Total bars: {len(df)}")
    print(f"Williams Highs: {result['is_williams_high'].sum()}")
    print(f"Williams Lows: {result['is_williams_low'].sum()}")
    print(f"Long positions: {result['is_long'].sum()}")
    print(f"Short positions: {result['is_short'].sum()}")
    print(f"Current position: {'Long' if result['is_long'].iloc[-1] else 'Short'}")

if __name__ == "__main__":
    plot_williams_fractal()
