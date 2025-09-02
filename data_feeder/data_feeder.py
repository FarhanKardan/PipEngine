import ssl
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

class DataFeeder:
    
    def __init__(self, username=None, password=None):
        self.logger = get_logger("DataFeeder")
        ssl._create_default_https_context = ssl._create_unverified_context
        self.username = username
        self.password = password
        self.tv = None
        self._connect()
    
    def _connect(self):
        try:
            if self.username and self.password:
                self.tv = TvDatafeed(self.username, self.password)
                self.logger.info("Connected to TradingView with authentication")
            else:
                self.tv = TvDatafeed()
                self.logger.info("Connected to TradingView without authentication")
        except Exception as e:
            try:
                self.tv = TvDatafeed()
                self.logger.warning(f"Initial connection failed, retrying: {e}")
            except Exception as e2:
                self.logger.error(f"Failed to connect to TradingView: {e2}")
                pass
    
    def _get_interval(self, interval_minutes):
        """Convert minutes to tvDatafeed Interval"""
        interval_map = {
            1: Interval.in_1_minute,
            5: Interval.in_5_minute,
            15: Interval.in_15_minute,
            30: Interval.in_30_minute,
            60: Interval.in_1_hour,
            240: Interval.in_4_hour,
            1440: Interval.in_daily,
        }
        return interval_map.get(interval_minutes, Interval.in_1_hour)
    
    def fetch_data(self, symbol, exchange='OANDA', interval_minutes=60, n_bars=500):
        """Fetch data with interval in minutes"""
        if not self.tv:
            self.logger.error("TradingView connection not available")
            return None
        
        try:
            interval = self._get_interval(interval_minutes)
            self.logger.info(f"Fetching {n_bars} bars for {symbol} ({interval_minutes}min)")
            df = self.tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                n_bars=n_bars
            )
            if df is not None and not df.empty:
                self.logger.info(f"Successfully fetched {len(df)} bars for {symbol}")
                return df
            else:
                self.logger.warning(f"No data received for {symbol}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None
    
    def filter_by_date(self, df, start_date, end_date):
        """Filter dataframe by date range"""
        if df is None or df.empty:
            self.logger.warning("No data to filter")
            return None
        
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            self.logger.info(f"Filtering data from {start_date} to {end_date}")
            
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                filtered_df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
            else:
                df.index = pd.to_datetime(df.index)
                filtered_df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            self.logger.info(f"Filtered to {len(filtered_df)} bars")
            return filtered_df
        except Exception as e:
            self.logger.error(f"Failed to filter data by date: {e}")
            return None
    
    def get_data(self, symbol, start_date, end_date, interval_minutes=60, n_bars=5000):
        """Main method: fetch data and filter by date range"""
        df = self.fetch_data(symbol, interval_minutes=interval_minutes, n_bars=n_bars)
        return self.filter_by_date(df, start_date, end_date)
    


if __name__ == "__main__":
    feeder = DataFeeder()
    df = feeder.get_data('XAUUSD', '2025-01-01', '2025-01-02', interval_minutes=60)
    if df is not None:
        print(f"Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")