"""
Generic Data Manager

This module provides a unified interface for retrieving market data from various sources.
It abstracts data retrieval logic and provides consistent data format for the backtester.
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DEFAULT_SYMBOL, DEFAULT_TIMEFRAME, DEFAULT_START_DATE, DEFAULT_END_DATE
from data_feeder import DataFeeder

class DataManager:
    def __init__(self, data_source: str = None):
        self.data_source = data_source or "csv"
        self.data_feeder = DataFeeder()
        
    def get_data(self, 
                 symbol: str = None,
                 start_date: str = None,
                 end_date: str = None,
                 timeframe: str = None,
                 bars: int = None,
                 **kwargs) -> pd.DataFrame:
        
        symbol = symbol or DEFAULT_SYMBOL
        start_date = start_date or DEFAULT_START_DATE
        end_date = end_date or DEFAULT_END_DATE
        timeframe = timeframe or DEFAULT_TIMEFRAME
        bars = bars or 1000
        
        print(f"📊 Retrieving data from {self.data_source.upper()} source")
        print(f"📈 Symbol: {symbol}, Timeframe: {timeframe}")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"📊 Bars: {bars}")
        
        try:
            if self.data_source == "csv":
                return self._get_data_from_csv(symbol, start_date, end_date, timeframe, bars)
            else:
                return self._get_data_from_feeder(symbol, start_date, end_date, timeframe, bars, **kwargs)
                
        except Exception as e:
            print(f"❌ Error retrieving data: {e}")
            print("🔄 Falling back to data feeder")
            return self._get_data_from_feeder(symbol, start_date, end_date, timeframe, bars, **kwargs)
    
    def _get_data_from_csv(self, symbol: str, start_date: str, end_date: str, 
                           timeframe: str, bars: int) -> pd.DataFrame:
        try:
            csv_path = "results/data/klines.csv"
            if not os.path.exists(csv_path):
                print(f"⚠️ CSV file not found: {csv_path}")
                print("🔄 Using data feeder instead")
                return self._get_data_from_feeder(symbol, start_date, end_date, timeframe, bars)
            
            df = pd.read_csv(csv_path)
            
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
            
            if start_date and end_date:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            if bars and len(df) > bars:
                df = df.tail(bars)
            
            print(f"✅ CSV data loaded: {len(df)} bars")
            return df
            
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return self._get_data_from_feeder(symbol, start_date, end_date, timeframe, bars)
    
    def _get_data_from_feeder(self, symbol: str, start_date: str, end_date: str, 
                              timeframe: str, bars: int, **kwargs) -> pd.DataFrame:
        print("🔄 Using data feeder")
        return self.data_feeder.fetch_xauusd(bars=bars)
    
    def validate_data(self, df: pd.DataFrame, required_columns: list = None) -> bool:
        if df is None or df.empty:
            return False
        
        required_columns = required_columns or ['open', 'high', 'low', 'close']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        print("✅ Data validation passed")
        return True
