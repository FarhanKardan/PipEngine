"""
MetaTrader Client Module

This module provides communication with MetaTrader through the REST API.
Based on the API documentation from: http://trade-api.reza-developer.com/docs/v1
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
import json


class MetaTraderClient:
    """
    MetaTrader REST API Client
    
    Provides methods to communicate with MetaTrader for:
    - Price history retrieval
    - Account information
    - Trading operations
    """
    
    def __init__(self, base_url: str = "http://trade-api.reza-developer.com", 
                 api_key: Optional[str] = None):
        """
        Initialize the MetaTrader client
        
        Args:
            base_url: Base URL for the MetaTrader API
            api_key: API key for authentication (if required)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to the MetaTrader API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get_price_history(self, symbol: str, timeframe: str = "M1", 
                         start_time: Optional[Union[str, datetime]] = None,
                         end_time: Optional[Union[str, datetime]] = None,
                         count: Optional[int] = None) -> pd.DataFrame:
        """
        Get price history for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD", "EURUSD")
            timeframe: Timeframe for the data (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            start_time: Start time for data retrieval
            end_time: End time for data retrieval
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        endpoint = "/api/v1/price-history"
        
        # Prepare parameters
        params = {
            "symbol": symbol,
            "timeframe": timeframe
        }
        
        if start_time:
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            params["startTime"] = start_time
            
        if end_time:
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            params["endTime"] = end_time
            
        if count:
            params["count"] = count
        
        # Make API request
        response = self._make_request("GET", endpoint, params=params)
        data = response.json()
        
        # Convert to DataFrame
        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            
            # Convert timestamp to datetime
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], unit='ms')
                df.set_index('time', inplace=True)
            
            # Ensure proper column names
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'tick_volume': 'tick_volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            return df
        else:
            return pd.DataFrame()
    
    def get_account_info(self) -> Dict:
        """
        Get account information
        
        Returns:
            Dictionary containing account details
        """
        endpoint = "/api/v1/account"
        response = self._make_request("GET", endpoint)
        return response.json()
    
    def get_symbols(self) -> List[Dict]:
        """
        Get available trading symbols
        
        Returns:
            List of available symbols with their details
        """
        endpoint = "/api/v1/symbols"
        response = self._make_request("GET", endpoint)
        return response.json()
    
    def get_server_time(self) -> datetime:
        """
        Get server time
        
        Returns:
            Server datetime
        """
        endpoint = "/api/v1/server-time"
        response = self._make_request("GET", endpoint)
        data = response.json()
        
        if 'serverTime' in data:
            return datetime.fromtimestamp(data['serverTime'] / 1000)
        else:
            raise Exception("Could not retrieve server time")
    
    def place_order(self, symbol: str, order_type: str, volume: float,
                   price: Optional[float] = None, stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None, comment: str = "") -> Dict:
        """
        Place a trading order
        
        Args:
            symbol: Trading symbol
            order_type: Order type (BUY, SELL, BUY_LIMIT, SELL_LIMIT, etc.)
            volume: Order volume
            price: Order price (for limit orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            
        Returns:
            Order response from API
        """
        endpoint = "/api/v1/orders"
        
        order_data = {
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "comment": comment
        }
        
        if price:
            order_data["price"] = price
        if stop_loss:
            order_data["stopLoss"] = stop_loss
        if take_profit:
            order_data["takeProfit"] = take_profit
        
        response = self._make_request("POST", endpoint, json=order_data)
        return response.json()
    
    def get_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        endpoint = "/api/v1/orders"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        response = self._make_request("GET", endpoint, params=params)
        return response.json()
    
    def close_order(self, order_id: int) -> Dict:
        """
        Close an open order
        
        Args:
            order_id: ID of the order to close
            
        Returns:
            Response from API
        """
        endpoint = f"/api/v1/orders/{order_id}"
        response = self._make_request("DELETE", endpoint)
        return response.json()
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open positions
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open positions
        """
        endpoint = "/api/v1/positions"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        response = self._make_request("GET", endpoint, params=params)
        return response.json()
    
    def close_position(self, position_id: int) -> Dict:
        """
        Close an open position
        
        Args:
            position_id: ID of the position to close
            
        Returns:
            Response from API
        """
        endpoint = f"/api/v1/positions/{position_id}"
        response = self._make_request("DELETE", endpoint)
        return response.json()
    
    def test_connection(self) -> bool:
        """
        Test connection to the MetaTrader API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.get_server_time()
            return True
        except Exception:
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'session'):
            self.session.close()
