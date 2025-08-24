# Strategies package for PipEngine
# Contains trading strategies that use indicators and data

# Import the actual strategy functions we have
from .strategy_1.ema_fractal_strategy_plot import (
    load_and_prepare_data,
    add_ema,
    williams_fractal_trailing_stops,
    calculate_strategy_positions
)

__version__ = '1.0.0'
__all__ = [
    'load_and_prepare_data',
    'add_ema', 
    'williams_fractal_trailing_stops',
    'calculate_strategy_positions'
]
