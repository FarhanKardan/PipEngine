import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import DEFAULT_SYMBOL, DEFAULT_TIMEFRAME

class DataFeeder:
    """Data feeder for market data"""
    
    def __init__(self):
        """Initialize the data feeder"""
        pass
    
    def fetch_data(self, symbol=None, timeframe=None, bars=1000):
        """Fetch market data"""
        if symbol is None:
            symbol = DEFAULT_SYMBOL
        if timeframe is None:
            timeframe = DEFAULT_TIMEFRAME
            
        print(f"📊 Fetching {bars} bars of {timeframe} data for {symbol}")
        
        try:
            # For now, we'll use a simple approach
            # In a real implementation, you'd connect to your data source
            print("⚠️  This is a placeholder implementation")
            print("📝 Please implement actual data fetching logic")
            
            # Return sample data structure
            return self._create_sample_data(symbol, bars)
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
    
    def fetch_xauusd(self, **kwargs):
        """Fetch XAUUSD data - convenience method"""
        return self.fetch_data('XAUUSD', **kwargs)
    
    def _create_sample_data(self, symbol, bars):
        """Create sample data for testing purposes"""
        # Generate sample data with realistic structure
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=bars)  # Use hours instead of days
        
        # Create datetime range - fix the parameters
        date_range = pd.date_range(start=start_date, end=end_date, periods=bars)
        
        # Create sample OHLCV data
        import numpy as np
        np.random.seed(42)  # For reproducible results
        
        base_price = 3300.0  # Base price for XAUUSD
        price_changes = np.random.normal(0, 5, bars)  # Random price changes
        prices = base_price + np.cumsum(price_changes)
        
        # Create OHLCV data
        data = {
            'datetime': date_range,
            'symbol': [symbol] * bars,
            'open': prices + np.random.normal(0, 1, bars),
            'high': prices + np.random.normal(2, 1, bars),
            'low': prices + np.random.normal(-2, 1, bars),
            'close': prices,
            'volume': np.random.randint(100, 1000, bars)
        }
        
        df = pd.DataFrame(data)
        
        # Ensure high >= open, close and low <= open, close
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        print(f"✅ Generated sample data: {len(df)} bars")
        return df

if __name__ == "__main__":
    feeder = DataFeeder()
    
    # Test data fetching
    df = feeder.fetch_xauusd(bars=100)
    
    if df is not None:
        print(f"Data: {df.shape[0]} bars, {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")
        print(f"Sample data:")
        print(df.head())
        
        # Save to CSV
        output_file = "results/data/klines.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Data saved to {output_file}")
        print(f"📊 Total records: {len(df)}")
        print(f"📅 Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    else:
        print("Failed to fetch data")
