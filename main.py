#!/usr/bin/env python3
"""
Main application - fetches XAUUSD data, calculates indicators, exports to CSV and plots
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Import indicators
from indicators.ema import calculate_ema
from indicators.dema import calculate_dema
from indicators.atr import calculate_atr
from indicators.enhanced_zero_lag_macd import enhanced_zero_lag_macd
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

# Import data feeder
import sys
sys.path.append('data feeder')
from data_feeder import DataFeeder

def plot_chart(df, result_df):
    """Create chart with price and indicators"""
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('XAUUSD Technical Analysis', fontweight='bold', fontsize=16)
    
    # Plot 1: Price with EMAs
    ax1 = axes[0, 0]
    ax1.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1)
    ax1.plot(result_df.index, result_df['EMA_9'], label='EMA(9)', color='blue', linewidth=1)
    ax1.plot(result_df.index, result_df['DEMA_9'], label='DEMA(9)', color='red', linewidth=1)
    ax1.set_title('Price with Moving Averages')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: ATR
    ax2 = axes[0, 1]
    ax2.plot(result_df.index, result_df['ATR_14'], label='ATR(14)', color='purple', linewidth=1)
    ax2.set_title('Average True Range')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Enhanced Zero Lag MACD
    ax3 = axes[1, 0]
    ax3.plot(result_df.index, result_df['zero_lag_macd'], label='MACD Line', color='blue', linewidth=1)
    ax3.plot(result_df.index, result_df['signal'], label='Signal', color='red', linewidth=1)
    ax3.bar(result_df.index, result_df['histogram'], label='Histogram', color='gray', alpha=0.5)
    ax3.set_title('Enhanced Zero Lag MACD')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Williams Fractal Trailing Stops
    ax4 = axes[1, 1]
    ax4.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1)
    ax4.plot(result_df.index, result_df['williams_long_stop_plot'], 
             label='Long Stop', color='green', linewidth=2)
    ax4.plot(result_df.index, result_df['williams_short_stop_plot'], 
             label='Short Stop', color='red', linewidth=2)
    ax4.set_title('Williams Fractal Trailing Stops')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in axes.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

def main():
    try:
        print("🚀 Starting Technical Analysis")
        print("=" * 50)
        
        # Initialize and fetch data
        feeder = DataFeeder()
        df = feeder.fetch_xauusd()
        
        if df is None or df.empty:
            print("❌ No data received")
            return
        
        print(f"✅ Fetched {len(df)} bars of XAUUSD data")
        
        # Calculate indicators
        print("📊 Calculating Technical Indicators...")
        
        # Basic indicators
        ema_9 = calculate_ema(df['close'], 9)
        dema_9 = calculate_dema(df['close'], 9)
        atr_14 = calculate_atr(df, 14, 'RMA')
        
        # Advanced indicators
        enhanced_macd = enhanced_zero_lag_macd(df, 12, 26, 9, 9, True, False)
        williams_fractal = williams_fractal_trailing_stops(df, 2, 2, 0, "Close")
        
        # Combine data
        result_df = df.copy()
        result_df['EMA_9'] = ema_9
        result_df['DEMA_9'] = dema_9
        result_df['ATR_14'] = atr_14
        
        # Add enhanced MACD columns
        for col in enhanced_macd.columns:
            result_df[col] = enhanced_macd[col]
        
        # Add Williams fractal columns
        for col in williams_fractal.columns:
            result_df[col] = williams_fractal[col]
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"XAUUSD_Analysis_{timestamp}.csv"
        result_df.to_csv(filename, index=True)
        print(f"💾 Data saved: {len(result_df)} rows to {filename}")
        
        # Create plot
        print("📈 Creating chart...")
        fig = plot_chart(df, result_df)
        
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
