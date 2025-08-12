import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

class EmaFractalStrategy:
    """
    EMA Fractal Strategy
    
    Strategy Logic:
    - If close price is above EMA value: Look for short position at last candle's high
    - If close price is below EMA value: Look for long position at last candle's low
    - Uses Williams Fractal Trailing Stops for entry/exit signals
    """
    
    def __init__(self, ema_period=200, fractal_left_range=2, fractal_right_range=2, buffer_percent=0):
        """
        Initialize EMA Fractal Strategy
        
        Args:
            ema_period (int): Period for EMA calculation
            fractal_left_range (int): Williams fractal left range
            fractal_right_range (int): Williams fractal right range
            buffer_percent (float): Buffer percentage for fractal stops
        """
        self.ema_period = ema_period
        self.fractal_left_range = fractal_left_range
        self.fractal_right_range = fractal_right_range
        self.buffer_percent = buffer_percent
    
    def calculate_signals(self, df):
        """
        Calculate trading signals based on EMA and Williams Fractal
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC data
            
        Returns:
            pd.DataFrame: DataFrame with strategy signals and positions
        """
        # Calculate EMA
        ema = calculate_ema(df['close'], self.ema_period)
        
        # Calculate Williams Fractal Trailing Stops
        fractal_result = williams_fractal_trailing_stops(
            df, 
            self.fractal_left_range, 
            self.fractal_right_range, 
            self.buffer_percent, 
            'Close'
        )
        
        # Initialize strategy signals
        signals = pd.DataFrame(index=df.index)
        signals['ema'] = ema
        signals['close_above_ema'] = df['close'] > ema
        signals['close_below_ema'] = df['close'] < ema
        
        # Strategy logic
        signals['ema_trend'] = np.where(signals['close_above_ema'], 'Bearish', 'Bullish')
        
        # Position signals
        signals['long_signal'] = False
        signals['short_signal'] = False
        signals['entry_price'] = np.nan
        signals['stop_loss'] = np.nan
        signals['position_type'] = 'None'
        
        # Generate entry signals
        for i in range(1, len(df)):
            # Short position: Close above EMA, look for short at last candle's high
            if signals['close_above_ema'].iloc[i]:
                if fractal_result['is_williams_high'].iloc[i]:
                    signals.loc[signals.index[i], 'short_signal'] = True
                    signals.loc[signals.index[i], 'entry_price'] = df['high'].iloc[i]
                    signals.loc[signals.index[i], 'stop_loss'] = fractal_result['williams_high_price'].iloc[i]
                    signals.loc[signals.index[i], 'position_type'] = 'Short'
            
            # Long position: Close below EMA, look for long at last candle's low
            else:
                if fractal_result['is_williams_low'].iloc[i]:
                    signals.loc[signals.index[i], 'long_signal'] = True
                    signals.loc[signals.index[i], 'entry_price'] = df['low'].iloc[i]
                    signals.loc[signals.index[i], 'stop_loss'] = fractal_result['williams_low_price'].iloc[i]
                    signals.loc[signals.index[i], 'position_type'] = 'Long'
        
        # Add Williams Fractal data
        for col in fractal_result.columns:
            signals[f'fractal_{col}'] = fractal_result[col]
        
        return signals
    
    def get_current_position(self, signals):
        """
        Get current trading position and recommendations
        
        Args:
            signals (pd.DataFrame): Strategy signals DataFrame
            
        Returns:
            dict: Current position information
        """
        if signals.empty:
            return {'position': 'None', 'recommendation': 'No data available'}
        
        latest = signals.iloc[-1]
        
        if latest['long_signal']:
            return {
                'position': 'Long',
                'entry_price': latest['entry_price'],
                'stop_loss': latest['stop_loss'],
                'recommendation': f"Go LONG at {latest['entry_price']:.2f}, Stop Loss: {latest['stop_loss']:.2f}",
                'ema_trend': latest['ema_trend']
            }
        elif latest['short_signal']:
            return {
                'position': 'Short',
                'entry_price': latest['entry_price'],
                'stop_loss': latest['stop_loss'],
                'recommendation': f"Go SHORT at {latest['entry_price']:.2f}, Stop Loss: {latest['stop_loss']:.2f}",
                'ema_trend': latest['ema_trend']
            }
        else:
            return {
                'position': 'None',
                'recommendation': f"Hold - Current trend: {latest['ema_trend']}",
                'ema_trend': latest['ema_trend']
            }
    
    def backtest(self, df, initial_capital=10000):
        """
        Simple backtest of the strategy
        
        Args:
            df (pd.DataFrame): Historical data
            initial_capital (float): Initial capital for backtesting
            
        Returns:
            dict: Backtest results
        """
        signals = self.calculate_signals(df)
        
        # Initialize backtest variables
        capital = initial_capital
        position = 'None'
        entry_price = 0
        stop_loss = 0
        trades = []
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            
            # Check for stop loss hit
            if position == 'Long' and current_price <= stop_loss:
                # Long position stopped out
                loss = (stop_loss - entry_price) / entry_price
                capital *= (1 + loss)
                trades.append({
                    'type': 'Long',
                    'entry': entry_price,
                    'exit': stop_loss,
                    'result': 'Stop Loss',
                    'pnl': loss
                })
                position = 'None'
                
            elif position == 'Short' and current_price >= stop_loss:
                # Short position stopped out
                loss = (current_price - stop_loss) / stop_loss
                capital *= (1 - loss)
                trades.append({
                    'type': 'Short',
                    'entry': entry_price,
                    'exit': stop_loss,
                    'result': 'Stop Loss',
                    'pnl': -loss
                })
                position = 'None'
            
            # Check for new signals
            if position == 'None':
                if signals['long_signal'].iloc[i]:
                    position = 'Long'
                    entry_price = signals['entry_price'].iloc[i]
                    stop_loss = signals['stop_loss'].iloc[i]
                elif signals['short_signal'].iloc[i]:
                    position = 'Short'
                    entry_price = signals['entry_price'].iloc[i]
                    stop_loss = signals['stop_loss'].iloc[i]
        
        # Calculate final results
        total_return = (capital - initial_capital) / initial_capital * 100
        win_trades = [t for t in trades if t['pnl'] > 0]
        loss_trades = [t for t in trades if t['pnl'] < 0]
        
        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return_pct': total_return,
            'total_trades': len(trades),
            'winning_trades': len(win_trades),
            'losing_trades': len(loss_trades),
            'win_rate': len(win_trades) / len(trades) if trades else 0,
            'trades': trades
        }

def run_ema_fractal_strategy(df, ema_period=200, fractal_left_range=2, fractal_right_range=2, buffer_percent=0):
    """
    Convenience function to run EMA Fractal Strategy
    
    Args:
        df (pd.DataFrame): OHLC data
        ema_period (int): EMA period
        fractal_left_range (int): Fractal left range
        fractal_right_range (int): Fractal right range
        buffer_percent (float): Buffer percentage
        
    Returns:
        tuple: (signals, current_position, backtest_results)
    """
    strategy = EmaFractalStrategy(ema_period, fractal_left_range, fractal_right_range, buffer_percent)
    
    # Calculate signals
    signals = strategy.calculate_signals(df)
    
    # Get current position
    current_position = strategy.get_current_position(signals)
    
    # Run backtest
    backtest_results = strategy.backtest(df)
    
    return signals, current_position, backtest_results

if __name__ == "__main__":
    # Test the strategy
    print("🧪 Testing EMA Fractal Strategy...")
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Run strategy
    signals, position, backtest = run_ema_fractal_strategy(sample_data)
    
    print(f"✅ Strategy test completed!")
    print(f"Current position: {position['position']}")
    print(f"Recommendation: {position['recommendation']}")
    print(f"Backtest results: {backtest['total_return_pct']:.2f}% return")
