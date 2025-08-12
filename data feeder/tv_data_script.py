import ssl
import certifi
import pandas as pd
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

def fetch_xauusd_data():
    """
    Fetch XAUUSD data from OANDA exchange
    
    Returns:
    pandas.DataFrame: DataFrame with XAUUSD data or None if failed
    """
    username = 'mohammadtrade1404@gmail.com'
    password = 'YourTradingViewPassword'
    
    try:
        tv = TvDatafeed(username, password)
        df = tv.get_hist(symbol='XAUUSD', exchange='OANDA', interval=Interval.in_1_hour, n_bars=500)
        print("✅ Data fetched with authentication")
        return df
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Trying without authentication...")
        try:
            tv = TvDatafeed()
            df = tv.get_hist(symbol='XAUUSD', exchange='OANDA', interval=Interval.in_1_hour, n_bars=500)
            print("✅ Data fetched without authentication")
            return df
        except Exception as e2:
            print(f"Failed to fetch data: {e2}")
            return None

if __name__ == "__main__":
    # Test the function
    df = fetch_xauusd_data()
    
    if df is not None:
        print(f"\n📊 Data Summary:")
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df.index.min()} to {df.index.max()}")
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"XAUUSD_OANDA_1H_{timestamp}.csv"
        df.to_csv(filename, index=True)
        print(f"\n✅ Data saved to: {filename}")
    else:
        print("❌ Failed to fetch data")
