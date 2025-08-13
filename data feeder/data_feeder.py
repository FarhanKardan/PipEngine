import ssl
import pandas as pd
import time
from tvDatafeed import TvDatafeed, Interval

class DataFeeder:
    """Simple data feeder for TradingView data"""
    
    def __init__(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        self.tv = TvDatafeed()
    
    def fetch_data(self, symbol: str, exchange: str = 'OANDA', 
                   interval: Interval = Interval.in_1_hour, n_bars: int = 5000, max_retries=3):
        """Fetch data for a symbol with retry logic"""
        for attempt in range(max_retries):
            try:
                df = self.tv.get_hist(symbol=symbol, exchange=exchange, 
                                     interval=interval, n_bars=n_bars)
                if df is not None and not df.empty:
                    return df
                else:
                    print(f"Attempt {attempt + 1}: No data received")
            except Exception as e:
                print(f"Attempt {attempt + 1}: Error fetching {symbol}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
            return None
    
    def fetch_xauusd(self, **kwargs):
        """Fetch XAUUSD data"""
        return self.fetch_data('XAUUSD', **kwargs)

if __name__ == "__main__":
    feeder = DataFeeder()
    # Use 5-minute timeframe
    df = feeder.fetch_xauusd(interval=Interval.in_5_minute)
    
    if df is not None:
        print(f"Data: {df.shape[0]} bars, {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")
        print(f"Sample data:")
        print(df.head())
        df.to_csv("klines.csv")
        print("✅ Data saved to klines.csv")
    else:
        print("Failed to fetch data")
