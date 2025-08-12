#!/usr/bin/env python3
"""
Main application - fetches XAUUSD data, calculates one indicator from each type, exports to CSV and plots on one chart
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'indicators'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'data feeder'))

# Import one indicator from each type
from indicators.ema import calculate_ema
from indicators.dema import calculate_dema
from indicators.atr import calculate_atr
from data_feeder import DataFeeder

def plot_simple_chart(df, result_df):
    """Create one simple chart with all indicators"""
    
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot candlesticks
    for i in range(len(df)):
        color = 'green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red'
        ax.vlines(df.index[i], df['low'].iloc[i], df['high'].iloc[i], color=color, linewidth=1)
        ax.vlines(df.index[i], df['open'].iloc[i], df['close'].iloc[i], color=color, linewidth=2)
    
    # Plot indicators
    ax.plot(result_df.index, result_df['EMA_9'], label='EMA(9)', color='blue', linewidth=1)
    ax.plot(result_df.index, result_df['DEMA_9'], label='DEMA(9)', color='red', linewidth=1)
    ax.plot(result_df.index, result_df['ATR_14'], label='ATR(14)', color='purple', linewidth=1)
    
    ax.set_title('XAUUSD with Technical Indicators', fontweight='bold')
    ax.set_ylabel('Price (USD)')
    ax.set_xlabel('Date')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

def main():
    try:
        print("🚀 Starting Simple Technical Analysis")
        print("=" * 50)
        
        # Initialize and fetch data
        feeder = DataFeeder('mohammadtrade1404@gmail.com', 'YourTradingViewPassword')
        df = feeder.fetch_xauusd()
        
        if df is None or df.empty:
            print("❌ No data received")
            return
        
        print(f"✅ Fetched {len(df)} bars of XAUUSD data")
        
        # Calculate one indicator from each type
        print("📊 Calculating Technical Indicators...")
        
        ema_9 = calculate_ema(df['close'], 9)
        dema_9 = calculate_dema(df['close'], 9)
        atr_14 = calculate_atr(df, 14, 'RMA')
        
        # Combine data
        result_df = df.copy()
        result_df['EMA_9'] = ema_9
        result_df['DEMA_9'] = dema_9
        result_df['ATR_14'] = atr_14
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"XAUUSD_Simple_Analysis_{timestamp}.csv"
        result_df.to_csv(filename, index=True)
        print(f"💾 Data saved: {len(result_df)} rows to {filename}")
        
        # Create plot
        print("📈 Creating chart...")
        fig = plot_simple_chart(df, result_df)
        
        # Save plot
        plot_filename = f"XAUUSD_Chart_{timestamp}.png"
        fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"🖼️ Chart saved to: {plot_filename}")
        
        print(f"\n✅ Analysis Complete!")
        print(f"📁 CSV: {filename}")
        print(f"🖼️ Chart: {plot_filename}")
        
        # Show plot
        plt.show()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
