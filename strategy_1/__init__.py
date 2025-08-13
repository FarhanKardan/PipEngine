"""
Strategy 1: EMA + Williams Fractal Analysis
"""

from .ema_fractal_plot import main, load_and_prepare_data, add_ema
from .ema_fractal_strategy import calculate_strategy_positions, create_plot

__all__ = [
    'main', 
    'load_and_prepare_data', 
    'add_ema',
    'calculate_strategy_positions',
    'create_plot'
]
__version__ = '1.0.0'
