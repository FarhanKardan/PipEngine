# Strategies package for PipEngine
# Contains trading strategies that use indicators and data

from .ema_fractal_strategy import EmaFractalStrategy, run_ema_fractal_strategy

__version__ = '1.0.0'
__all__ = [
    'EmaFractalStrategy',
    'run_ema_fractal_strategy'
]
