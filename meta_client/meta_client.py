import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Union
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

class MetaTraderClient:
    
    def __init__(self, base_url: str = "http://trade-api.reza-developer.com", 
                 api_key: Optional[str] = None):
        self.logger = get_logger("MetaTraderClient")
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
            self.logger.info("MetaTrader client initialized with API key")
        else:
            self.logger.info("MetaTrader client initialized without API key")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            self.logger.debug(f"Request successful: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {e}")
    
    def get_price_history(self, symbol: str, timeframe: str, 
                         from_date: str, to_date: str) -> pd.DataFrame:
        
        endpoint = "/v1/meta/history/price"
        
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "from_date": from_date,
            "to_date": to_date
        }
        
        self.logger.info(f"Getting price history for {symbol} ({timeframe}) from {from_date} to {to_date}")
        response = self._make_request("GET", endpoint, params=params)
        data = response.json()
        
        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], unit='ms')
                df.set_index('time', inplace=True)
            
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'tick_volume': 'tick_volume'
            }
            
            df = df.rename(columns=column_mapping)
            self.logger.info(f"Retrieved {len(df)} bars for {symbol}")
            return df
        else:
            self.logger.warning(f"No data received for {symbol}")
            return pd.DataFrame()
    
    def get_quote(self, symbol: str) -> Dict:
        endpoint = "/v1/meta/quote"
        
        params = {
            "symbol": symbol
        }
        
        self.logger.info(f"Getting quote for {symbol}")
        response = self._make_request("GET", endpoint, params=params)
        data = response.json()
        self.logger.info(f"Quote retrieved for {symbol}: {data.get('bid', 'N/A')}/{data.get('ask', 'N/A')}")
        return data
    
    def place_order(self, symbol: str, order_type: str, volume: float,
                   price: Optional[float] = None, sl: Optional[float] = None,
                   tp: Optional[float] = None, comment: str = "",
                   async_order: bool = True, magic: int = 0,
                   expiration: Optional[str] = None, type_filling: str = "") -> Dict:
        endpoint = "/v1/meta/order"
        
        order_data = {
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "async": async_order,
            "comment": comment,
            "magic": magic,
            "type_filling": type_filling
        }
        
        if price is not None:
            order_data["price"] = price
        if sl is not None:
            order_data["sl"] = sl
        if tp is not None:
            order_data["tp"] = tp
        if expiration:
            order_data["expiration"] = expiration
        
        self.logger.info(f"Placing {order_type} order for {symbol} volume {volume}")
        response = self._make_request("POST", endpoint, json=order_data)
        data = response.json()
        self.logger.info(f"Order placed: {data.get('order', 'N/A')}")
        return data
    
    def test_connection(self) -> bool:
        try:
            self.logger.info("Testing MetaTrader connection")
            response = self._make_request("GET", "/v1/meta/history/price", 
                                        params={"symbol": "EURUSD", "timeframe": "PERIOD_M1", 
                                               "from_date": "2025.01.21 17:10:00", 
                                               "to_date": "2025.01.21 17:15:00"})
            self.logger.info("MetaTrader connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"MetaTrader connection test failed: {e}")
            return False
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()