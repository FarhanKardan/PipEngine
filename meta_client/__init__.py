"""
MetaTrader Client Package

This package provides communication with MetaTrader through the REST API.
Supports price history, account information, and trading operations.
"""

from .meta_client import MetaTraderClient

__version__ = "1.0.0"
__all__ = ["MetaTraderClient"]
