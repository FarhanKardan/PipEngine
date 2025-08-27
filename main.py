#!/usr/bin/env python3
"""
Main application - fetches XAUUSD data, calculates indicators, exports to CSV and runs EMA Fractal Strategy
"""

import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(__file__))

# Import indicators
from indicators.ema import calculate_ema
from indicators.dema import calculate_dema
from indicators.atr import calculate_atr
from indicators.enhanced_zero_lag_macd import enhanced_zero_lag_macd
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

# Import data feeder
from data_feeder.data_feeder import DataFeeder

# Import EMA Fractal Strategy
from strategies.strategy_1 import add_ema, calculate_strategy_positions

def apply_ema_fractal_strategy(df):
    """Apply EMA Fractal Strategy to the dataframe"""
    try:
        print("🧮 Applying EMA Fractal Strategy...")
        
        # Add EMA 200
        df, ema_col = add_ema(df, period=200, price_col='close')
        
        # Calculate Williams Fractal Trailing Stops
        wft_df = williams_fractal_trailing_stops(df, 9, 9, 0, "Close")
        df = df.join(wft_df)
        
        # Calculate strategy positions
        df['strategy_position'] = calculate_strategy_positions(df, ema_col)
        
        # Calculate strategy performance metrics
        long_positions = (df['strategy_position'] == 1).sum()
        short_positions = (df['strategy_position'] == -1).sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        total_positions = long_positions + short_positions
        
        print(f"✅ Strategy applied successfully!")
        print(f"📊 Positions: {long_positions} long, {short_positions} short, {neutral_positions} neutral")
        print(f"📈 Total active positions: {total_positions}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error applying EMA Fractal Strategy: {e}")
        return df

def main():
    """Main application function with improved error handling and logging"""
    try:
        print("🚀 Starting Technical Analysis with EMA Fractal Strategy")
        print("=" * 60)
        
        # Initialize and fetch data
        print("📊 Initializing data feeder...")
        feeder = DataFeeder()
        
        print("📈 Fetching XAUUSD data...")
        df = feeder.fetch_xauusd()
        
        if df is None or df.empty:
            print("❌ No data received from feeder")
            return
        
        print(f"✅ Fetched {len(df)} bars of XAUUSD data")
        print(f"📅 Data range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Calculate indicators
        print("🧮 Calculating Technical Indicators...")
        
        try:
            # Basic indicators
            print("  📊 Calculating EMA...")
            ema_9 = calculate_ema(df['close'], 9)
            
            print("  📊 Calculating DEMA...")
            dema_9 = calculate_dema(df['close'], 9)
            
            print("  📊 Calculating ATR...")
            atr_14 = calculate_atr(df, 14, 'RMA')
            
            # Advanced indicators
            print("  📊 Calculating Enhanced MACD...")
            enhanced_macd = enhanced_zero_lag_macd(df, 12, 26, 9, 9, True, False)
            
            print("  📊 Calculating Williams Fractal...")
            williams_fractal = williams_fractal_trailing_stops(df, 2, 2, 0, "Close")
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            print("🔄 Continuing with available indicators...")
            # Set default values for failed indicators
            ema_9 = pd.Series([0] * len(df), index=df.index)
            dema_9 = pd.Series([0] * len(df), index=df.index)
            atr_14 = pd.Series([0] * len(df), index=df.index)
            enhanced_macd = pd.DataFrame({'zero_lag_macd': [0] * len(df), 'signal': [0] * len(df), 'histogram': [0] * len(df)}, index=df.index)
            williams_fractal = pd.DataFrame({'williams_long_stop_plot': [0] * len(df), 'williams_short_stop_plot': [0] * len(df)}, index=df.index)
        
        # Combine data
        print("🔗 Combining data...")
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
        
        # Apply EMA Fractal Strategy
        result_df = apply_ema_fractal_strategy(result_df)
        
        # Save to CSV
        print("💾 Saving data to CSV...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/data/XAUUSD_Analysis_{timestamp}.csv"
        
        # Ensure results directory exists
        os.makedirs("results/data", exist_ok=True)
        
        result_df.to_csv(filename, index=True)
        print(f"✅ Data saved: {len(result_df)} rows to {filename}")
        
        print(f"\n✅ Analysis Complete!")
        print(f"📁 CSV: {filename}")
        
    except Exception as e:
        print(f"❌ Critical error in main application: {e}")
        print("🔍 Error details:")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting tips:")
        print("   - Check if all dependencies are installed")
        print("   - Verify data feeder is working")
        print("   - Ensure results directory exists")
        print("   - Check Python version compatibility")

def run_ema_fractal_backtest():
    """Run EMA Fractal Strategy backtesting with performance analysis"""
    try:
        print("\n" + "=" * 80)
        print("🚀 EMA FRACTAL STRATEGY BACKTESTING")
        print("=" * 80)
        
        # Import backtesting components
        from backtester.backtester import GenericBacktester
        from strategies.ema_fractal_wrapper import EmaFractalStrategy
        from config import DEFAULT_INITIAL_CAPITAL, DEFAULT_COMMISSION, DEFAULT_POSITION_SIZE
        
        print("📊 Initializing backtester...")
        backtester = GenericBacktester(
            initial_capital=10000,
            commission=0.001,
            position_size=0.2
        )
        
        print("📈 Setting up EMA Fractal Strategy...")
        strategy = EmaFractalStrategy(
            ema_period=200,
            left_range=9,
            right_range=9
        )
        
        print(f"✅ Strategy: {strategy.name}")
        print(f"⚙️ Parameters: {strategy.parameters}")
        print(f"💰 Capital: ${backtester.initial_capital:,.2f}")
        print(f"💸 Commission: {backtester.commission*100:.2f}%")
        print(f"📊 Position Size: {backtester.position_size}")
        
        print("\n🔄 Running backtest...")
        results = backtester.run_backtest(
            strategy=strategy,
            symbol="XAUUSD",
            bars=500,
            timeframe="M1"
        )
        
        if results:
            print("\n💾 Exporting results...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backtest_dir = f"results/backtests/ema_fractal_backtest_{timestamp}"
            backtester.export_results(results, backtest_dir)
            print("✅ Backtest completed successfully!")
            print(f"📁 Results saved to: {backtest_dir}")
            
            # Display performance summary
            if 'performance_metrics' in results:
                metrics = results['performance_metrics']
                print("\n📊 PERFORMANCE SUMMARY:")
                print("=" * 50)
                print(f"💰 Total Return: {metrics.get('total_return', 0):.2f}%")
                print(f"📈 Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                print(f"📉 Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
                print(f"🔄 Total Trades: {metrics.get('total_trades', 0)}")
                print(f"✅ Win Rate: {metrics.get('win_rate', 0):.2f}%")
                print(f"📊 Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                print(f"💵 Final Capital: ${metrics.get('final_capital', 0):,.2f}")
        else:
            print("❌ Backtest failed!")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all backtesting modules are available")
    except Exception as e:
        print(f"❌ Backtest error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    
    # Ask user if they want to run EMA Fractal Strategy backtesting
    try:
        response = input("\n🤔 Would you like to run EMA Fractal Strategy backtesting? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            run_ema_fractal_backtest()
        else:
            print("👋 Backtesting skipped. Goodbye!")
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"❌ Error in user input: {e}")
        print("👋 Exiting...")
