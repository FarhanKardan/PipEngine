import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from strategies.strategy_interface import StrategyInterface
from strategies.strategy_1.ema_fractal_strategy import add_ema, williams_fractal_trailing_stops, calculate_strategy_positions

class EmaFractalStrategy(StrategyInterface):
    def __init__(self, ema_period=200, left_range=9, right_range=9, **kwargs):
        super().__init__(name="EMA + Williams Fractal Strategy", **kwargs)
        self.ema_period = ema_period
        self.left_range = left_range
        self.right_range = right_range
        self.parameters.update({
            'ema_period': ema_period,
            'left_range': left_range,
            'right_range': right_range
        })
        self.signal_columns = ['entry_signal']
        self.position_columns = ['strategy_position']
        self.stop_loss_columns = ['williams_long_stop_plot', 'williams_short_stop_plot']
    
    def calculate_signals(self, df):
        df = df.copy()
        
        df, ema_col = add_ema(df, period=self.ema_period, price_col='close')
        
        wft_df = williams_fractal_trailing_stops(
            df, 
            left_range=self.left_range, 
            right_range=self.right_range, 
            buffer_percent=0, 
            flip_on="Close"
        )
        df = df.join(wft_df)
        
        df['entry_signal'] = 0
        return df
    
    def calculate_positions(self, df):
        df = df.copy()
        
        ema_col = f'ema_{self.ema_period}'
        df['strategy_position'] = calculate_strategy_positions(df, ema_col)
        
        return df
