"""
Generic Backtester Module

This module provides a generic backtesting framework that works with any strategy
that implements the StrategyInterface. It retrieves data based on configuration
and returns comprehensive performance metrics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import sys
import os
import json

# Add the project root to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the generic data manager and strategy interface
from data_feeder.data_manager import DataManager
from strategies.strategy_interface import StrategyInterface
from .performance_analyzer import PerformanceAnalyzer

# Import config
from config import (
    DEFAULT_INITIAL_CAPITAL, 
    DEFAULT_COMMISSION, 
    DEFAULT_MAX_ROWS,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_TIMEFRAME,
    DEFAULT_POSITION_SIZE
)


class GenericBacktester:
    """
    Generic Backtester Class
    
    Provides comprehensive backtesting capabilities for any strategy that implements
    the StrategyInterface. Works with configuration-based data retrieval and
    returns detailed performance metrics.
    """
    
    def __init__(self, 
                 initial_capital: float = None,
                 commission: float = None,
                 position_size: float = None,
                 data_source: str = None):
        """
        Initialize the generic backtester
        
        Args:
            initial_capital: Starting capital for the backtest
            commission: Commission rate per trade (0.001 = 0.1%)
            position_size: Fixed position size for each trade
            data_source: Data source type ('csv', 'api', 'database', 'realtime')
        """
        self.initial_capital = initial_capital or DEFAULT_INITIAL_CAPITAL
        self.commission = commission or DEFAULT_COMMISSION
        self.position_size = position_size or DEFAULT_POSITION_SIZE
        self.data_source = data_source
        
        # Initialize components
        self.data_manager = DataManager(data_source=data_source)
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Reset state
        self.reset()
        
    def reset(self):
        """Reset the backtester to initial state"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.current_positions = {}
        
    def run_backtest(self, 
                    strategy: StrategyInterface,
                    symbol: str = None,
                    start_date: str = None,
                    end_date: str = None,
                    timeframe: str = None,
                    bars: int = None,
                    **kwargs) -> Dict:
        """
        Run a complete backtest for any strategy
        
        Args:
            strategy: StrategyInterface instance
            symbol: Trading symbol to backtest
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Timeframe for analysis
            bars: Number of bars to retrieve
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing backtest results and performance metrics
        """
        print(f"🚀 Starting Generic Backtest")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        print(f"💸 Commission: {self.commission*100:.2f}%")
        print(f"📊 Position Size: {self.position_size}")
        print("=" * 60)
        
        # Reset backtester
        self.reset()
        
        try:
            if strategy is None:
                raise ValueError("Strategy must be provided")
            
            print(f"📈 Strategy: {strategy.name}")
            print(f"⚙️ Parameters: {strategy.parameters}")
            
            # Retrieve data based on configuration
            print("📊 Retrieving market data...")
            df = self.data_manager.get_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                bars=bars,
                **kwargs
            )
            
            if df is None or df.empty:
                raise ValueError("No data retrieved for the specified period")
            
            # Validate data
            if not self.data_manager.validate_data(df, strategy.required_columns):
                raise ValueError(f"Data validation failed for strategy: {strategy.name}")
            
            print(f"✅ Data retrieved: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"📅 Date range: {df.index.min()} to {df.index.max()}")
            
            # Apply strategy to data
            print("🧮 Applying strategy...")
            df = strategy.apply_strategy(df)
            
            # Validate strategy output
            if not self._validate_strategy_output(df, strategy):
                raise ValueError(f"Strategy output validation failed for: {strategy.name}")
            
            print(f"✅ Strategy applied successfully")
            print(f"📊 Strategy columns: {[col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]}")
            
            # Run the backtest simulation
            print("🔄 Running backtest simulation...")
            self._simulate_trading(df, strategy)
            
            # Analyze performance
            print("📈 Analyzing performance...")
            performance_metrics = self.performance_analyzer.calculate_metrics(
                self.trades, 
                self.equity_curve, 
                self.initial_capital
            )
            
            # Prepare comprehensive results
            results = self._prepare_results(df, strategy, performance_metrics)
            
            # Print summary
            self._print_summary(results)
            
            # Print detailed trade information
            self._print_trade_details(results)
            
            return results
            
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _validate_strategy_output(self, df: pd.DataFrame, strategy: StrategyInterface) -> bool:
        """
        Validate that the strategy output contains required columns
        
        Args:
            df: DataFrame with strategy output
            strategy: Strategy instance
            
        Returns:
            True if validation passes, False otherwise
        """
        # Check required columns
        missing_columns = [col for col in strategy.required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        # Check signal columns
        missing_signals = [col for col in strategy.signal_columns if col not in df.columns]
        if missing_signals:
            print(f"❌ Missing signal columns: {missing_signals}")
            return False
        
        # Check position columns
        missing_positions = [col for col in strategy.position_columns if col not in df.columns]
        if missing_positions:
            print(f"❌ Missing position columns: {missing_positions}")
            return False
        
        return True
    
    def _simulate_trading(self, df: pd.DataFrame, strategy: StrategyInterface):
        """Simulate trading based on strategy positions"""
        self.trades = []
        self.equity_curve = []
        
        # Get the main position column (use first one if multiple)
        position_col = strategy.position_columns[0]
        
        # Track single position
        current_trade = None
        
        for i in range(len(df)):
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            current_position = df[position_col].iloc[i]
            previous_position = df[position_col].iloc[i-1] if i > 0 else 0
            
            # Update equity curve
            self._update_equity(df.index[i], current_price, current_trade)
            
            # Handle new position entry (when position changes from 0 to non-zero)
            if previous_position == 0 and current_position != 0 and current_trade is None:
                # Determine if it's a long or short entry
                is_long = current_position > 0
                is_short = current_position < 0
                
                if is_long or is_short:
                    # Open new position
                    entry_price = current_price
                    commission = entry_price * self.position_size * self.commission
                    
                    trade_type = 'LONG' if is_long else 'SHORT'
                    
                    current_trade = {
                        'entry_time': current_time,
                        'entry_price': entry_price,
                        'size': self.position_size,
                        'type': trade_type,
                        'commission': commission,
                        'position_id': len(self.trades) + 1,
                        'strategy': strategy.name
                    }
                    
                    self.trades.append(current_trade)
                    print(f"📈 Opened {trade_type.lower()} position at {current_time}: {self.position_size} lots @ ${entry_price:.2f}")
            
            # Handle position exit (when position changes from non-zero to 0)
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
    
    def _prepare_results(self, df: pd.DataFrame, strategy: StrategyInterface, 
                        performance_metrics: Dict) -> Dict:
        """
        Prepare comprehensive backtest results
        
        Args:
            df: DataFrame with strategy data
            strategy: Strategy instance
            performance_metrics: Performance analysis results
            
        Returns:
            Dictionary with complete backtest results
        """
        # Calculate final capital
        final_capital = self.capital
        if self.equity_curve:
            final_capital = self.equity_curve[-1]['equity']
        
        # Get strategy info
        strategy_info = strategy.get_strategy_info()
        
        # Prepare results
        results = {
            'backtest_info': {
                'strategy_name': strategy.name,
                'strategy_parameters': strategy.parameters,
                'strategy_info': strategy_info,
                'initial_capital': self.initial_capital,
                'final_capital': final_capital,
                'total_return': (final_capital - self.initial_capital) / self.initial_capital * 100,
                'commission_rate': self.commission,
                'position_size': self.position_size
            },
            'data_info': {'shape': df.shape, 'columns': list(df.columns)},
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'performance_metrics': performance_metrics,
            'strategy_columns': {
                'signal_columns': strategy.signal_columns,
                'position_columns': strategy.position_columns,
                'stop_loss_columns': strategy.stop_loss_columns,
                'take_profit_columns': strategy.take_profit_columns
            }
        }
        
        return results
    
    def _print_summary(self, results: Dict):
        """Print backtest summary"""
        print("\n" + "=" * 60)
        print("📊 BACKTEST SUMMARY")
        print("=" * 60)
        
        info = results['backtest_info']
        metrics = results['performance_metrics']
        
        print(f"Strategy: {info['strategy_name']}")
        print(f"Parameters: {info['strategy_parameters']}")
        print(f"Initial Capital: ${info['initial_capital']:,.2f}")
        print(f"Final Capital: ${info['final_capital']:,.2f}")
        print(f"Total Return: {info['total_return']:.2f}%")
        print(f"Total Trades: {len(results['trades'])}")
        print(f"Commission Rate: {info['commission_rate']*100:.2f}%")
        print(f"Position Size: {info['position_size']}")
        
        if metrics:
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.3f}")
            print(f"   Max Drawdown: {metrics.get('max_drawdown', 'N/A'):.2f}%")
            print(f"   Win Rate: {metrics.get('win_rate', 'N/A'):.1f}%")
            print(f"   Profit Factor: {metrics.get('profit_factor', 'N/A'):.2f}")
            print(f"   Average Trade: ${metrics.get('avg_trade', 'N/A'):.2f}")
        
        print("=" * 60)
    
    def _print_trade_details(self, results: Dict):
        """Print detailed trade information"""
        print("\n📋 TRADE DETAILS:")
        print("=" * 80)
        if results['trades']:
            trades_df = pd.DataFrame(results['trades'])
            print(trades_df.to_string(index=False))
        else:
            print("No trades executed")
    
    def export_results(self, results: Dict, filename: str = None):
        """
        Export backtest results to files
        
        Args:
            results: Backtest results dictionary
            filename: Base filename for export (without extension)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            strategy_name = results['backtest_info']['strategy_name'].replace(' ', '_').lower()
            filename = f"backtest_{strategy_name}_{timestamp}"
        
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
            metrics_filename = f"{filename}_metrics.json"
            with open(metrics_filename, 'w') as f:
                json.dump(results['performance_metrics'], f, indent=2, default=str)
            print(f"💾 Performance metrics exported to: {metrics_filename}")
        
        # Export complete results to JSON
        complete_filename = f"{filename}_complete.json"
        # Convert datetime objects to strings for JSON serialization
        exportable_results = self._make_json_serializable(results)
        with open(complete_filename, 'w') as f:
            json.dump(exportable_results, f, indent=2, default=str)
        print(f"💾 Complete results exported to: {complete_filename}")
        
        print(f"✅ All results exported with base filename: {filename}")
    
    def _make_json_serializable(self, obj):
        """Convert object to JSON serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj


def main():
    """Example usage of the generic backtester"""
    
    print("🧪 Generic Backtester Ready")
    print("=" * 50)
    print("Use this backtester with any strategy that implements StrategyInterface")
    print("See example_usage.py for usage examples")


if __name__ == "__main__":
    main()
