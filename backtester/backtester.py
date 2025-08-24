"""
Main Backtester Module

This module provides the core backtesting functionality for trading strategies.
It integrates with data feeder and strategies to simulate trading performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import sys
import os

# Add the project root to the path to import strategies and data feeder
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the required functions directly from the strategy file
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies', 'strategy_1'))
from ema_fractal_strategy_plot import (
    load_and_prepare_data, 
    add_ema, 
    williams_fractal_trailing_stops,
    calculate_strategy_positions
)
from performance_analyzer import PerformanceAnalyzer

# Import config
from config import (
    DEFAULT_INITIAL_CAPITAL, 
    DEFAULT_COMMISSION, 
    DEFAULT_MAX_ROWS,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_TIMEFRAME
)


class Backtester:
    """
    Main Backtester Class
    
    Provides comprehensive backtesting capabilities for trading strategies.
    Integrates with data feeder and strategies to analyze performance.
    """
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        """
        Initialize the backtester
        
        Args:
            initial_capital: Starting capital for the backtest
            commission: Commission rate per trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
        
    def reset(self):
        """Reset the backtester to initial state"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.current_positions = {}
        
    def run_backtest(self, 
                    csv_path: str,
                    symbol: str,
                    start_date: str,
                    end_date: str,
                    timeframe: str = "M1",
                    max_rows: Optional[int] = None) -> Dict:
        """
        Run a complete backtest for the specified period
        
        Args:
            csv_path: Path to the CSV data file
            symbol: Trading symbol to backtest
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Timeframe for analysis
            max_rows: Maximum number of rows to analyze
            
        Returns:
            Dictionary containing backtest results and performance metrics
        """
        print(f"🚀 Starting Backtest for {symbol}")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        print(f"💸 Commission: {self.commission*100:.2f}%")
        print("=" * 60)
        
        # Reset backtester
        self.reset()
        
        try:
            # Load and prepare data
            print("📊 Loading data...")
            df = load_and_prepare_data(csv_path, symbol, start_date, end_date, max_rows)
            
            if df is None or df.empty:
                raise ValueError("No data loaded for the specified period")
            
            print(f"✅ Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"📈 Date range: {df.index.min()} to {df.index.max()}")
            
            # Add technical indicators
            print("🧮 Calculating indicators...")
            df, ema_col = add_ema(df, period=200, price_col='close')
            
            # Calculate Williams Fractal Trailing Stops
            wft_df = williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
            df = df.join(wft_df)
            
            # Calculate strategy positions
            df = calculate_strategy_positions(df, ema_col)
            
            # Run the backtest simulation
            print("🔄 Running backtest simulation...")
            self._simulate_trading(df)
            
            # Analyze performance
            print("📈 Analyzing performance...")
            analyzer = PerformanceAnalyzer()
            performance_metrics = analyzer.calculate_metrics(
                self.trades, 
                self.equity_curve, 
                self.initial_capital
            )
            
            # Prepare results
            results = {
                'backtest_info': {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'timeframe': timeframe,
                    'initial_capital': self.initial_capital,
                    'final_capital': self.capital,
                    'total_return': (self.capital - self.initial_capital) / self.initial_capital * 100
                },
                'trades': self.trades,
                'equity_curve': self.equity_curve,
                'performance_metrics': performance_metrics,
                'data_summary': {
                    'total_bars': len(df),
                    'date_range': f"{df.index.min()} to {df.index.max()}",
                    'strategy_positions': df['strategy_position'].max(),
                    'entry_signals': df['entry_signal'].sum()
                }
            }
            
            # Print summary
            self._print_summary(results)
            
            # Print detailed trade information
            print("\n📋 TRADE DETAILS:")
            print("=" * 80)
            if results['trades']:
                trades_df = pd.DataFrame(results['trades'])
                print(trades_df.to_string(index=False))
            else:
                print("No trades executed")
            
            return results
            
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _simulate_trading(self, df: pd.DataFrame):
        """Simulate trading based on strategy positions"""
        self.trades = []
        self.equity_curve = []
        
        # Track single position
        current_trade = None
        
        for i in range(len(df)):
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            current_position = df['strategy_position'].iloc[i]  # 1 for long, -1 for short, 0 for no position
            previous_position = df['strategy_position'].iloc[i-1] if i > 0 else 0
            
            # Update equity curve
            self._update_equity(current_time, current_price, current_trade)
            
            # Handle new position entry (when position changes from 0 to 1 or -1)
            if previous_position == 0 and current_position != 0 and current_trade is None:
                # Determine if it's a long or short entry
                is_long = current_position == 1
                is_short = current_position == -1
                
                if is_long or is_short:
                    # Open new position
                    position_size = 0.1  # Fixed position size
                    entry_price = current_price
                    commission = entry_price * position_size * self.commission
                    
                    trade_type = 'LONG' if is_long else 'SHORT'
                    
                    current_trade = {
                        'entry_time': current_time,
                        'entry_price': entry_price,
                        'size': position_size,
                        'type': trade_type,
                        'commission': commission,
                        'position_id': len(self.trades) + 1
                    }
                    
                    self.trades.append(current_trade)
                    print(f"📈 Opened {trade_type.lower()} position at {current_time}: {position_size} lots @ ${entry_price:.2f}")
            
            # Handle position exit (when position changes from 1 or -1 to 0)
            elif previous_position != 0 and current_position == 0 and current_trade is not None:
                # Calculate P&L
                entry_price = current_trade['entry_price']
                size = current_trade['size']
                
                if current_trade['type'] == 'LONG':
                    pnl = (current_price - entry_price) * size
                else:  # SHORT
                    pnl = (entry_price - current_price) * size
                
                commission_cost = current_price * size * self.commission
                net_pnl = pnl - commission_cost
                
                # Update trade record
                current_trade['exit_time'] = current_time
                current_trade['exit_price'] = current_price
                current_trade['pnl'] = pnl
                current_trade['net_pnl'] = net_pnl
                current_trade['commission_exit'] = commission_cost
                
                print(f"📉 Closed {current_trade['type'].lower()} position at {current_time}: {size} lots @ ${current_price:.2f}, P&L: ${net_pnl:.2f}")
                
                # Reset for next trade
                current_trade = None
        
        # Close any remaining open position at the end
        if current_trade is not None:
            final_price = df['close'].iloc[-1]
            
            # Calculate P&L
            entry_price = current_trade['entry_price']
            size = current_trade['size']
            
            if current_trade['type'] == 'LONG':
                pnl = (final_price - entry_price) * size
            else:  # SHORT
                pnl = (entry_price - final_price) * size
            
            commission_cost = final_price * size * self.commission
            net_pnl = pnl - commission_cost
            
            # Update trade record
            current_trade['exit_time'] = df.index[-1]
            current_trade['exit_price'] = final_price
            current_trade['pnl'] = pnl
            current_trade['net_pnl'] = net_pnl
            current_trade['commission_exit'] = commission_cost
            
            print(f"📉 Closed final {current_trade['type'].lower()} position at {df.index[-1]}: {size} lots @ ${final_price:.2f}, P&L: ${net_pnl:.2f}")
    
    def _update_equity(self, time: datetime, current_price: float, current_trade: Dict):
        """Update equity curve"""
        # Calculate current equity based on open position
        current_equity = self.capital
        
        # Add unrealized P&L from open position
        if current_trade is not None and 'exit_time' not in current_trade:
            entry_price = current_trade['entry_price']
            size = current_trade['size']
            
            if current_trade['type'] == 'LONG':
                unrealized_pnl = (current_price - entry_price) * size
            else:  # SHORT
                unrealized_pnl = (entry_price - current_price) * size
            
            current_equity += unrealized_pnl
        
        self.equity_curve.append({
            'time': time,
            'equity': current_equity,
            'price': current_price
        })
    
    def _print_summary(self, results: Dict):
        """Print backtest summary"""
        print("\n" + "=" * 60)
        print("📊 BACKTEST SUMMARY")
        print("=" * 60)
        
        info = results['backtest_info']
        metrics = results['performance_metrics']
        
        print(f"Symbol: {info['symbol']}")
        print(f"Period: {info['start_date']} to {info['end_date']}")
        print(f"Initial Capital: ${info['initial_capital']:,.2f}")
        print(f"Final Capital: ${info['final_capital']:,.2f}")
        print(f"Total Return: {info['total_return']:.2f}%")
        print(f"Total Trades: {len(results['trades'])}")
        
        if metrics:
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.3f}")
            print(f"   Max Drawdown: {metrics.get('max_drawdown', 'N/A'):.2f}%")
            print(f"   Win Rate: {metrics.get('win_rate', 'N/A'):.1f}%")
            print(f"   Profit Factor: {metrics.get('profit_factor', 'N/A'):.2f}")
            print(f"   Average Trade: ${metrics.get('avg_trade', 'N/A'):.2f}")
        
        print("=" * 60)
    
    def export_results(self, results: Dict, filename: str = None):
        """
        Export backtest results to files
        
        Args:
            results: Backtest results dictionary
            filename: Base filename for export (without extension)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{timestamp}"
        
        # Export trades to CSV
        if results.get('trades'):
            trades_df = pd.DataFrame(results['trades'])
            trades_filename = f"{filename}_trades.csv"
            trades_df.to_csv(trades_filename, index=False)
            print(f"💾 Trades exported to: {trades_filename}")
        
        # Export equity curve to CSV
        if results.get('equity_curve'):
            equity_df = pd.DataFrame(results['equity_curve'])
            equity_filename = f"{filename}_equity.csv"
            equity_df.to_csv(equity_filename, index=False)
            print(f"💾 Equity curve exported to: {equity_filename}")
        
        # Export performance metrics to JSON
        if results.get('performance_metrics'):
            import json
            metrics_filename = f"{filename}_metrics.json"
            with open(metrics_filename, 'w') as f:
                json.dump(results['performance_metrics'], f, indent=2, default=str)
            print(f"💾 Performance metrics exported to: {metrics_filename}")
        
        print(f"✅ All results exported with base filename: {filename}")


def main():
    """Example usage of the backtester"""
    
    # Initialize backtester with config values
    backtester = Backtester(
        initial_capital=DEFAULT_INITIAL_CAPITAL, 
        commission=DEFAULT_COMMISSION
    )
    
    # Run backtest with config values
    results = backtester.run_backtest(
        csv_path="results/data/klines.csv",
        symbol="OANDA:XAUUSD",
        start_date=DEFAULT_START_DATE,
        end_date=DEFAULT_END_DATE,
        timeframe=DEFAULT_TIMEFRAME,
        max_rows=DEFAULT_MAX_ROWS
    )
    
    # Export results to organized directory
    if results:
        backtester.export_results(results, "results/backtests/backtest_results")


if __name__ == "__main__":
    main()
