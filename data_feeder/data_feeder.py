import ssl
import pandas as pd
from tvDatafeed import TvDatafeed, Interval

class DataFeeder:
    
    def __init__(self, username=None, password=None):
        ssl._create_default_https_context = ssl._create_unverified_context
        self.username = username
        self.password = password
        self.tv = None
        self._connect()
    
    def _connect(self):
        try:
            if self.username and self.password:
                self.tv = TvDatafeed(self.username, self.password)
            else:
                self.tv = TvDatafeed()
        except Exception:
            try:
                self.tv = TvDatafeed()
            except Exception:
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
            return None
        
        try:
            interval = self._get_interval(interval_minutes)
            df = self.tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                n_bars=n_bars
            )
            return df if df is not None and not df.empty else None
        except Exception:
            return None
    
    def filter_by_date(self, df, start_date, end_date):
        """Filter dataframe by date range"""
        if df is None or df.empty:
            return None
        
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                return df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
            else:
                df.index = pd.to_datetime(df.index)
                return df[(df.index >= start_date) & (df.index <= end_date)]
        except Exception:
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