"""
Example usage of the MetaTrader Client

This script demonstrates how to use the MetaTraderClient class
to communicate with MetaTrader through the REST API.
"""

from meta_client import MetaTraderClient
from datetime import datetime, timedelta
import pandas as pd

def main():
    """Example usage of the MetaTrader client"""
    
    # Initialize the client
    # Replace with your actual API key if required
    client = MetaTraderClient(
        base_url="http://trade-api.reza-developer.com",
        api_key=None  # Add your API key here if required
    )
    
    print("=== MetaTrader Client Example ===\n")
    
    # Test connection
    print("Testing connection...")
    if client.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    
    # Get server time
    try:
        server_time = client.get_server_time()
        print(f"🕐 Server time: {server_time}")
    except Exception as e:
        print(f"❌ Could not get server time: {e}")
    
    # Get available symbols
    try:
        symbols = client.get_symbols()
        print(f"📊 Available symbols: {len(symbols)} found")
        if symbols:
            print(f"   Sample symbols: {[s.get('name', 'N/A') for s in symbols[:5]]}")
    except Exception as e:
        print(f"❌ Could not get symbols: {e}")
    
    # Get price history for XAUUSD
    try:
        print("\n📈 Getting price history for XAUUSD...")
        
        # Get last 100 bars
        df = client.get_price_history(
            symbol="XAUUSD",
            timeframe="M1",
            count=100
        )
        
        if not df.empty:
            print(f"✅ Retrieved {len(df)} bars")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Latest close: {df['close'].iloc[-1]:.2f}")
            
            # Save to CSV for analysis
            filename = f"xauusd_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename)
            print(f"💾 Data saved to: {filename}")
        else:
            print("❌ No data retrieved")
            
    except Exception as e:
        print(f"❌ Could not get price history: {e}")
    
    # Get account information
    try:
        print("\n💰 Getting account information...")
        account_info = client.get_account_info()
        print(f"✅ Account info retrieved")
        print(f"   Account: {account_info.get('login', 'N/A')}")
        print(f"   Balance: {account_info.get('balance', 'N/A')}")
        print(f"   Equity: {account_info.get('equity', 'N/A')}")
    except Exception as e:
        print(f"❌ Could not get account info: {e}")
    
    # Get open positions
    try:
        print("\n📊 Getting open positions...")
        positions = client.get_positions()
        print(f"✅ Found {len(positions)} open positions")
        for pos in positions:
            print(f"   {pos.get('symbol', 'N/A')}: {pos.get('type', 'N/A')} "
                  f"{pos.get('volume', 'N/A')} @ {pos.get('price', 'N/A')}")
    except Exception as e:
        print(f"❌ Could not get positions: {e}")
    
    print("\n=== Example completed ===")

if __name__ == "__main__":
    main()
