"""
Backtester Package

This package provides comprehensive backtesting capabilities for trading strategies.
Integrates with data feeder and strategies to analyze performance metrics.
"""

from .backtester import Backtester
from .performance_analyzer import PerformanceAnalyzer

__version__ = "1.0.0"
__all__ = ["Backtester", "PerformanceAnalyzer"]
