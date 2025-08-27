"""
Generic Strategy Interface

This module defines the interface that all trading strategies must implement
to work with the generic backtester. This allows for easy strategy development
and testing without modifying the core backtesting engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd

class StrategyInterface(ABC):
    """
    Abstract base class for all trading strategies
    
    All strategies must implement these methods to work with the generic backtester.
    This ensures consistency and allows for easy strategy development and testing.
    """
    
    def __init__(self, name: str = "Generic Strategy", **kwargs):
        """
        Initialize the strategy
        
        Args:
            name: Strategy name
            **kwargs: Strategy-specific parameters
        """
        self.name = name
        self.parameters = kwargs
        self.required_columns = ['open', 'high', 'low', 'close']
        self.signal_columns = ['signal']
        self.position_columns = ['position']
        self.stop_loss_columns = []
        self.take_profit_columns = []
        
    @abstractmethod
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals for the given data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added signal columns
        """
        pass
    
    @abstractmethod
    def calculate_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate position sizes based on signals
        
        Args:
            df: DataFrame with signals
            
        Returns:
            DataFrame with added position columns
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that the data contains required columns
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if df is None or df.empty:
            return False
        
        # Check required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Strategy {self.name}: Missing required columns: {missing_columns}")
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the strategy
        
        Returns:
            Dictionary with strategy information
        """
        return {
            'name': self.name,
            'parameters': self.parameters,
            'required_columns': self.required_columns,
            'signal_columns': self.signal_columns,
            'position_columns': self.position_columns,
            'stop_loss_columns': self.stop_loss_columns,
            'take_profit_columns': self.take_profit_columns
        }
    
    def apply_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the complete strategy to the data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with all strategy columns added
        """
        if not self.validate_data(df):
            raise ValueError(f"Data validation failed for strategy: {self.name}")
        
        # Calculate signals
        df = self.calculate_signals(df)
        
        # Calculate positions
        df = self.calculate_positions(df)
        
        return df
