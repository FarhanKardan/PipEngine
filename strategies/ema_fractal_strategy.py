import pandas as pd
import numpy as np
import sys
import os
import mplfinance as mpf

# To silence FutureWarning about downcasting on fillna, ffill, bfill
pd.set_option('future.no_silent_downcasting', True)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from indicators.ema import calculate_ema

def williams_fractal_trailing_stops(df, left_range=9, right_range=9, buffer_percent=0.5, flip_on="Close"):
    """
    Improved Williams Fractal Trailing Stops function
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC data
        left_range (int): Left range for fractal calculation
        right_range (int): Right range for fractal calculation
        buffer_percent (float): Buffer percentage for trailing stops
        flip_on (str): Column to use for flip detection
        
    Returns:
        pd.DataFrame: DataFrame with fractal signals and trailing stops
    """
    n = len(df)
    df_out = pd.DataFrame(index=df.index)

    # Calculate the fractal highs: high is the max in window centered on current index
    is_williams_high = (df['high'] == df['high'].rolling(window=left_range + right_range + 1, center=True).max())

    # Calculate fractal lows: low is the min in the same window
    is_williams_low = (df['low'] == df['low'].rolling(window=left_range + right_range + 1, center=True).min())

    # Long and short stop plots
    df_out['williams_long_stop_plot'] = df['close'].rolling(window=5, min_periods=1).min() * (1 - buffer_percent / 100)
    df_out['williams_short_stop_plot'] = df['close'].rolling(window=5, min_periods=1).max() * (1 + buffer_percent / 100)

    df_out['is_williams_high'] = is_williams_high
    df_out['is_williams_low'] = is_williams_low
    df_out['williams_high_price'] = df['high'].where(is_williams_high)
    df_out['williams_low_price'] = df['low'].where(is_williams_low)

    return df_out

class EmaFractalStrategy:
    """
    Enhanced EMA Fractal Strategy
    
    Strategy Logic:
    - If close price is above EMA value: Look for short position at last candle's high
    - If close price is below EMA value: Look for long position at last candle's low
    - Uses improved Williams Fractal Trailing Stops for entry/exit signals
    - Includes mplfinance plotting capabilities
    """
    
    def __init__(self, ema_period=200, fractal_left_range=9, fractal_right_range=9, buffer_percent=0.5):
        """
        Initialize Enhanced EMA Fractal Strategy
        
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
        
        # Calculate improved Williams Fractal Trailing Stops
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
        Enhanced backtest of the strategy
        
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
    
    def plot_strategy(self, df, signals, title="EMA Fractal Strategy Analysis"):
        """
        Create mplfinance plot with strategy signals
        
        Args:
            df (pd.DataFrame): OHLC data
            signals (pd.DataFrame): Strategy signals
            title (str): Plot title
            
        Returns:
            matplotlib.figure.Figure: The plot figure
        """
        # Prepare data for mplfinance
        plot_df = df.copy()
        
        # Add EMA to the plot
        ema_plot = mpf.make_addplot(signals['ema'], color='blue', width=2)
        
        # Prepare fractal markers
        high_fractals = signals['fractal_williams_high_price'].copy()
        low_fractals = signals['fractal_williams_low_price'].copy()
        
        # Replace NaNs with None to avoid plotting issues
        high_fractals = high_fractals.where(signals['fractal_is_williams_high'], other=pd.NA)
        low_fractals = low_fractals.where(signals['fractal_is_williams_low'], other=pd.NA)
        
        # Convert pd.NA back to np.nan for mplfinance
        high_fractals = high_fractals.astype(float)
        low_fractals = low_fractals.astype(float)
        
        # Create addplots for fractal markers
        high_fractal_plot = mpf.make_addplot(high_fractals, type='scatter', markersize=100, marker='v', color='red')
        low_fractal_plot = mpf.make_addplot(low_fractals, type='scatter', markersize=100, marker='^', color='green')
        
        # Add trailing stops
        long_stop_plot = mpf.make_addplot(signals['fractal_williams_long_stop_plot'], color='green', linestyle='--', alpha=0.7)
        short_stop_plot = mpf.make_addplot(signals['fractal_williams_short_stop_plot'], color='red', linestyle='--', alpha=0.7)
        
        # Compose all addplots
        addplots = [ema_plot, high_fractal_plot, low_fractal_plot, long_stop_plot, short_stop_plot]
        
        # Create the plot
        fig, axes = mpf.plot(
            plot_df,
            type='candle',
            style='charles',
            addplot=addplots,
            title=title,
            ylabel='Price',
            volume=True,
            figsize=(16, 10),
            returnfig=True
        )
        
        return fig

def run_ema_fractal_strategy(df, ema_period=200, fractal_left_range=9, fractal_right_range=9, buffer_percent=0.5):
    """
    Convenience function to run Enhanced EMA Fractal Strategy
    
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
    # Test the enhanced strategy
    print("🧪 Testing Enhanced EMA Fractal Strategy...")
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Run enhanced strategy
    signals, position, backtest = run_ema_fractal_strategy(sample_data)
    
    print(f"✅ Enhanced strategy test completed!")
    print(f"Current position: {position['position']}")
    print(f"Recommendation: {position['recommendation']}")
    print(f"Backtest results: {backtest['total_return_pct']:.2f}% return")
    
    # Test plotting functionality
    try:
        strategy = EmaFractalStrategy()
        fig = strategy.plot_strategy(sample_data, signals, "Enhanced EMA Fractal Strategy Test")
        print("✅ Plotting functionality working!")
    except Exception as e:
        print(f"⚠️ Plotting functionality test failed: {e}")
