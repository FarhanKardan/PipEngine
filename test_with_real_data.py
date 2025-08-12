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

def fetch_last_month_data():
    """Fetch last month's data using the data feeder"""
    print("🌐 Fetching last month's market data...")
    
    try:
        # Import data feeder
        sys.path.append(os.path.join(os.path.dirname(__file__), 'data feeder'))
        from data_feeder import DataFeeder
        
        feeder = DataFeeder()
        
        # Calculate date range for last month
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Fetch hourly data for the last month (approximately 720 bars)
        df = feeder.fetch_data('XAUUSD', 'OANDA', n_bars=720, interval='1H')
        
        if df is not None and not df.empty:
            print(f"✅ Successfully fetched {df.shape[0]} bars of XAUUSD data")
            print(f"📊 Data range: {df.index.min()} to {df.index.max()}")
            print(f"💰 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            
            # Save data for reference
            df.to_csv('last_month_xauusd.csv')
            print("💾 Data saved to 'last_month_xauusd.csv'")
            
            return df
        else:
            print("❌ Failed to fetch data")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def analyze_strategy_performance(df, strategy_name="EMA Fractal Strategy - XAUUSD"):
    """Analyze strategy performance with real data"""
    print(f"\n📈 Analyzing {strategy_name}")
    print("=" * 60)
    
    # Test different EMA periods
    ema_periods = [50, 100, 200]
    results = {}
    
    for ema_period in ema_periods:
        print(f"\n📊 Testing EMA period: {ema_period}")
        
        strategy = EmaFractalStrategy(
            ema_period=ema_period,
            fractal_left_range=2,
            fractal_right_range=2,
            buffer_percent=0.1
        )
        
        # Calculate signals
        signals = strategy.calculate_signals(df)
        
        # Analyze signals
        long_signals = signals['long_signal'].sum()
        short_signals = signals['short_signal'].sum()
        bullish_periods = (signals['ema_trend'] == 'Bullish').sum()
        bearish_periods = (signals['ema_trend'] == 'Bearish').sum()
        
        print(f"  📈 Long signals: {long_signals}")
        print(f"  📉 Short signals: {short_signals}")
        print(f"  🟢 Bullish periods: {bullish_periods}")
        print(f"  🔴 Bearish periods: {bearish_periods}")
        
        # Get current position
        position = strategy.get_current_position(signals)
        print(f"  🎯 Current position: {position['position']}")
        print(f"  💡 Recommendation: {position['recommendation']}")
        
        # Run backtest
        backtest = strategy.backtest(df)
        print(f"  💰 Backtest return: {backtest['total_return_pct']:.2f}%")
        print(f"  🔄 Total trades: {backtest['total_trades']}")
        print(f"  🏆 Win rate: {backtest['win_rate']:.2f}")
        
        # Store results
        results[ema_period] = {
            'signals': signals,
            'position': position,
            'backtest': backtest,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'bullish_periods': bullish_periods,
            'bearish_periods': bearish_periods
        }
        
        if backtest['trades']:
            print(f"  📋 Recent trades:")
            for i, trade in enumerate(backtest['trades'][-3:]):  # Show last 3 trades
                print(f"    Trade {i+1}: {trade['type']} @ ${trade['entry']:.2f} → ${trade['exit']:.2f} ({trade['result']})")
    
    return results

def create_performance_plots(df, results):
    """Create comprehensive performance plots"""
    print("\n📊 Creating performance analysis plots...")
    
    # Create subplots
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    fig.suptitle('EMA Fractal Strategy Performance Analysis - XAUUSD (Last Month)', fontsize=16, fontweight='bold')
    
    # Plot 1: Price action and EMA trends
    ax1 = axes[0]
    ax1.plot(df.index, df['close'], label='XAUUSD Close', linewidth=1, alpha=0.8, color='blue')
    
    # Plot EMAs
    colors = ['orange', 'red', 'purple']
    for i, (ema_period, result) in enumerate(results.items()):
        ema_data = result['signals']['ema']
        ax1.plot(df.index, ema_data, label=f'EMA {ema_period}', linewidth=2, color=colors[i], alpha=0.8)
    
    ax1.set_title('XAUUSD Price Action and EMA Trends')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Trading signals
    ax2 = axes[1]
    ax2.plot(df.index, df['close'], label='XAUUSD Close', linewidth=1, alpha=0.7, color='blue')
    
    # Plot signals for best performing EMA period
    best_ema = max(results.keys(), key=lambda x: results[x]['backtest']['total_return_pct'])
    best_result = results[best_ema]
    
    # Plot long signals
    long_signals = best_result['signals'][best_result['signals']['long_signal']]
    if not long_signals.empty:
        ax2.scatter(long_signals.index, long_signals['entry_price'], 
                   color='green', marker='^', s=100, label=f'Long Entry (EMA {best_ema})', zorder=5)
        ax2.scatter(long_signals.index, long_signals['stop_loss'], 
                   color='red', marker='v', s=80, label=f'Long Stop Loss (EMA {best_ema})', zorder=5)
    
    # Plot short signals
    short_signals = best_result['signals'][best_result['signals']['short_signal']]
    if not short_signals.empty:
        ax2.scatter(short_signals.index, short_signals['entry_price'], 
                   color='red', marker='v', s=100, label=f'Short Entry (EMA {best_ema})', zorder=5)
        ax2.scatter(short_signals.index, short_signals['stop_loss'], 
                   color='green', marker='^', s=80, label=f'Short Stop Loss (EMA {best_ema})', zorder=5)
    
    ax2.set_title(f'Trading Signals - Best Performing EMA ({best_ema})')
    ax2.set_ylabel('Price (USD)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Performance comparison
    ax3 = axes[2]
    ema_periods = list(results.keys())
    returns = [results[ema]['backtest']['total_return_pct'] for ema in ema_periods]
    trade_counts = [results[ema]['backtest']['total_trades'] for ema in ema_periods]
    win_rates = [results[ema]['backtest']['win_rate'] * 100 for ema in ema_periods]
    
    x = np.arange(len(ema_periods))
    width = 0.25
    
    bars1 = ax3.bar(x - width, returns, width, label='Return (%)', color='skyblue')
    bars2 = ax3.bar(x, trade_counts, width, label='Total Trades', color='lightcoral')
    bars3 = ax3.bar(x + width, win_rates, width, label='Win Rate (%)', color='lightgreen')
    
    ax3.set_title('Strategy Performance Comparison')
    ax3.set_xlabel('EMA Period')
    ax3.set_ylabel('Value')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f'EMA {p}' for p in ema_periods])
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom')
    
    # Format x-axis dates
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

def main():
    """Main function to test strategy with real data"""
    print("🚀 EMA Fractal Strategy - Real Market Data Test")
    print("=" * 60)
    
    # Fetch real market data
    df = fetch_last_month_data()
    
    if df is None:
        print("❌ Cannot proceed without market data")
        return
    
    # Analyze strategy performance
    results = analyze_strategy_performance(df)
    
    # Create performance plots
    fig = create_performance_plots(df, results)
    
    # Save plots
    plt.savefig('ema_strategy_real_data_analysis.png', dpi=300, bbox_inches='tight')
    print("📊 Performance analysis plot saved as 'ema_strategy_real_data_analysis.png'")
    
    # Show plots
    plt.show()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 REAL DATA ANALYSIS SUMMARY")
    print("=" * 60)
    
    best_ema = max(results.keys(), key=lambda x: results[x]['backtest']['total_return_pct'])
    best_result = results[best_ema]
    
    print(f"🏆 Best performing EMA period: {best_ema}")
    print(f"💰 Best return: {best_result['backtest']['total_return_pct']:.2f}%")
    print(f"🔄 Total trades: {best_result['backtest']['total_trades']}")
    print(f"🏆 Win rate: {best_result['backtest']['win_rate']:.2f}")
    print(f"🎯 Current position: {best_result['position']['position']}")
    print(f"💡 Recommendation: {best_result['position']['recommendation']}")
    
    print("\n🎯 Strategy analysis with real market data complete!")

if __name__ == "__main__":
    main()
