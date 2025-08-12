import ssl
import pandas as pd
from tvDatafeed import TvDatafeed, Interval

class DataFeeder:
    """
    Lightweight data feeder class for fetching financial data from TradingView
    """
    
    def __init__(self, username: str = None, password: str = None):
        # Fix SSL certificate issues on macOS
        ssl._create_default_https_context = ssl._create_unverified_context
        
        self.username = username
        self.password = password
        self.tv = None
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Initialize TradingView connection"""
        try:
            if self.username and self.password:
                self.tv = TvDatafeed(self.username, self.password)
                print("✅ Connected with authentication")
            else:
                self.tv = TvDatafeed()
                print("ℹ️ Connected without authentication")
        except Exception as e:
            print(f"⚠️ Connection failed: {e}")
            # Try without authentication
            try:
                self.tv = TvDatafeed()
                print("✅ Connected without authentication")
            except Exception as e2:
                print(f"❌ Failed to connect: {e2}")
    
    def fetch_data(self, symbol: str, exchange: str = 'OANDA', 
                   interval: Interval = Interval.in_1_hour, n_bars: int = 500):
        """
        Fetch data for a specific symbol
        
        Args:
            symbol (str): Symbol to fetch (e.g., 'XAUUSD')
            exchange (str): Exchange name
            interval (Interval): Time interval
            n_bars (int): Number of bars to fetch
        
        Returns:
            pd.DataFrame: Fetched data or None if failed
        """
        if not self.tv:
            print("❌ No connection available")
            return None
        
        try:
            print(f"📊 Fetching {n_bars} bars of {symbol} from {exchange}")
            df = self.tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                n_bars=n_bars
            )
            
            if df is not None and not df.empty:
                print(f"✅ Successfully fetched {len(df)} bars")
                return df
            else:
                print("❌ No data received")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def fetch_xauusd(self, **kwargs):
        """Fetch XAUUSD data"""
        return self.fetch_data('XAUUSD', **kwargs)

# Backward compatibility function
def fetch_xauusd_data():
    """Backward compatibility function"""
    feeder = DataFeeder()
    return feeder.fetch_xauusd()

if __name__ == "__main__":
    # Test the class
    feeder = DataFeeder(
        username='mohammadtrade1404@gmail.com',
        password='YourTradingViewPassword'
    )
    
    df = feeder.fetch_xauusd()
    if df is not None:
        print(f"Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
