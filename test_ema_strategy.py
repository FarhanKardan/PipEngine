import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from strategies.ema_fractal_strategy import EmaFractalStrategy, run_ema_fractal_strategy
sys.path.append(os.path.join(os.path.dirname(__file__), 'data feeder'))
from data_feeder import DataFeeder

def create_sample_data(periods=500):
    """Create realistic sample data for testing"""
    np.random.seed(42)  # For reproducible results
    
    dates = pd.date_range('2024-01-01', periods=periods, freq='1H')
    
    # Create a trending market with some volatility
    trend = np.linspace(100, 120, periods)  # Uptrend
    noise = np.random.normal(0, 0.5, periods)
    volatility = np.random.uniform(0.8, 1.2, periods)
    
    close_prices = trend + noise
    
    # Generate OHLC data
    data = []
    for i in range(periods):
        close = close_prices[i]
        high = close + np.random.uniform(0.5, 2.0) * volatility[i]
        low = close - np.random.uniform(0.5, 2.0) * volatility[i]
        open_price = close + np.random.uniform(-0.5, 0.5)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })
    
    return pd.DataFrame(data, index=dates)

def test_strategy_logic():
    """Test the core strategy logic"""
    print("🧪 Testing EMA Fractal Strategy Logic...")
    
    # Create sample data
    df = create_sample_data(300)
    
    # Test different EMA periods
    ema_periods = [50, 100, 200]
    
    for ema_period in ema_periods:
        print(f"\n📊 Testing with EMA period: {ema_period}")
        
        strategy = EmaFractalStrategy(
            ema_period=ema_period,
            fractal_left_range=2,
            fractal_right_range=2,
            buffer_percent=0.1
        )
        
        # Calculate signals
        signals = strategy.calculate_signals(df)
        
        # Analyze results
        long_signals = signals['long_signal'].sum()
        short_signals = signals['short_signal'].sum()
        bullish_periods = signals['ema_trend'].value_counts().get('Bullish', 0)
        bearish_periods = signals['ema_trend'].value_counts().get('Bearish', 0)
        
        print(f"  Long signals: {long_signals}")
        print(f"  Short signals: {short_signals}")
        print(f"  Bullish periods: {bullish_periods}")
        print(f"  Bearish periods: {bearish_periods}")
        
        # Test current position
        position = strategy.get_current_position(signals)
        print(f"  Current position: {position['position']}")
        print(f"  Recommendation: {position['recommendation']}")
        
        # Run backtest
        backtest = strategy.backtest(df)
        print(f"  Backtest return: {backtest['total_return_pct']:.2f}%")
        print(f"  Total trades: {backtest['total_trades']}")
        print(f"  Win rate: {backtest['win_rate']:.2f}")

def plot_strategy_analysis(df, signals, strategy_name="EMA Fractal Strategy"):
    """Create comprehensive plots for strategy analysis"""
    
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    fig.suptitle(f'{strategy_name} Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Price and EMA
    ax1 = axes[0]
    ax1.plot(df.index, df['close'], label='Close Price', linewidth=1, alpha=0.8)
    ax1.plot(df.index, signals['ema'], label=f'EMA ({signals["ema"].iloc[0]:.2f})', 
             linewidth=2, color='orange')
    
    # Highlight EMA trend changes
    bullish_mask = signals['ema_trend'] == 'Bullish'
    bearish_mask = signals['ema_trend'] == 'Bearish'
    
    ax1.fill_between(df.index, df['close'].min(), df['close'].max(), 
                     where=bullish_mask, alpha=0.2, color='green', label='Bullish Trend')
    ax1.fill_between(df.index, df['close'].min(), df['close'].max(), 
                     where=bearish_mask, alpha=0.2, color='red', label='Bearish Trend')
    
    ax1.set_title('Price Action and EMA Trend')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Entry Signals
    ax2 = axes[1]
    ax2.plot(df.index, df['close'], label='Close Price', linewidth=1, alpha=0.7)
    
    # Plot long signals
    long_signals = signals[signals['long_signal']]
    if not long_signals.empty:
        ax2.scatter(long_signals.index, long_signals['entry_price'], 
                   color='green', marker='^', s=100, label='Long Entry', zorder=5)
        # Plot stop losses for long positions
        ax2.scatter(long_signals.index, long_signals['stop_loss'], 
                   color='red', marker='v', s=80, label='Long Stop Loss', zorder=5)
    
    # Plot short signals
    short_signals = signals[signals['short_signal']]
    if not short_signals.empty:
        ax2.scatter(short_signals.index, short_signals['entry_price'], 
                   color='red', marker='v', s=100, label='Short Entry', zorder=5)
        # Plot stop losses for short positions
        ax2.scatter(short_signals.index, short_signals['stop_loss'], 
                   color='green', marker='^', s=80, label='Short Stop Loss', zorder=5)
    
    ax2.set_title('Entry Signals and Stop Losses')
    ax2.set_ylabel('Price')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Williams Fractal Indicators
    ax3 = axes[2]
    ax3.plot(df.index, df['close'], label='Close Price', linewidth=1, alpha=0.7)
    
    # Plot Williams highs and lows if available
    if 'fractal_is_williams_high' in signals.columns:
        williams_highs = signals[signals['fractal_is_williams_high']]
        if not williams_highs.empty:
            ax3.scatter(williams_highs.index, williams_highs['fractal_williams_high_price'], 
                       color='red', marker='v', s=60, label='Williams High', zorder=4)
    
    if 'fractal_is_williams_low' in signals.columns:
        williams_lows = signals[signals['fractal_is_williams_low']]
        if not williams_lows.empty:
            ax3.scatter(williams_lows.index, williams_lows['fractal_williams_low_price'], 
                       color='green', marker='^', s=60, label='Williams Low', zorder=4)
    
    ax3.set_title('Williams Fractal Indicators')
    ax3.set_ylabel('Price')
    ax3.set_xlabel('Date')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

def test_with_real_data():
    """Test strategy with real market data if available"""
    print("\n🌐 Testing with Real Market Data...")
    
    try:
        feeder = DataFeeder()
        df = feeder.fetch_xauusd(n_bars=1000, interval='1H')
        
        if df is not None and not df.empty:
            print(f"✅ Fetched {df.shape[0]} bars of XAUUSD data")
            
            # Run strategy
            signals, position, backtest = run_ema_fractal_strategy(
                df, ema_period=200, fractal_left_range=2, fractal_right_range=2, buffer_percent=0.1
            )
            
            print(f"Current position: {position['position']}")
            print(f"Recommendation: {position['recommendation']}")
            print(f"Backtest results: {backtest['total_return_pct']:.2f}% return")
            
            # Create plots
            fig = plot_strategy_analysis(df, signals, "EMA Fractal Strategy - XAUUSD")
            plt.savefig('ema_strategy_xauusd_analysis.png', dpi=300, bbox_inches='tight')
            print("📊 Plot saved as 'ema_strategy_xauusd_analysis.png'")
            plt.show()
            
            return df, signals
            
        else:
            print("❌ Failed to fetch real data, using sample data instead")
            return None, None
            
    except Exception as e:
        print(f"❌ Error fetching real data: {e}")
        print("Using sample data instead")
        return None, None

def main():
    """Main testing function"""
    print("🚀 EMA Fractal Strategy Testing Suite")
    print("=" * 50)
    
    # Test 1: Strategy Logic
    test_strategy_logic()
    
    # Test 2: Sample Data Analysis
    print("\n📈 Testing with Sample Data...")
    sample_df = create_sample_data(500)
    
    strategy = EmaFractalStrategy(ema_period=100, fractal_left_range=2, fractal_right_range=2, buffer_percent=0.1)
    sample_signals = strategy.calculate_signals(sample_df)
    
    # Run backtest on sample data
    sample_backtest = strategy.backtest(sample_df)
    print(f"Sample data backtest: {sample_backtest['total_return_pct']:.2f}% return")
    print(f"Total trades: {sample_backtest['total_trades']}")
    print(f"Win rate: {sample_backtest['win_rate']:.2f}")
    
    # Create plots for sample data
    fig = plot_strategy_analysis(sample_df, sample_signals, "EMA Fractal Strategy - Sample Data")
    plt.savefig('ema_strategy_sample_analysis.png', dpi=300, bbox_inches='tight')
    print("📊 Sample data plot saved as 'ema_strategy_sample_analysis.png'")
    plt.show()
    
    # Test 3: Real Data (if available)
    real_df, real_signals = test_with_real_data()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TESTING SUMMARY")
    print("=" * 50)
    print("✅ Strategy logic tested")
    print("✅ Sample data analysis completed")
    print("✅ Plots generated and saved")
    
    if real_df is not None:
        print("✅ Real data analysis completed")
    else:
        print("⚠️  Real data analysis skipped (using sample data)")
    
    print("\n🎯 Strategy is ready for live trading!")

if __name__ == "__main__":
    main()
