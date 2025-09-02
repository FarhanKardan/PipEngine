from meta_client import MetaTraderClient

def main():
    client = MetaTraderClient(
        base_url="http://trade-api.reza-developer.com",
        api_key=None
    )
    
    print("=== MetaTrader Client Example ===\n")
    
    print("Testing connection...")
    if client.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    
    try:
        print("\n📈 Getting price history for EURUSD...")
        
        df = client.get_price_history(
            symbol="EURUSD",
            timeframe="PERIOD_M1",
            from_date="2025.01.21 17:10:00",
            to_date="2025.01.21 17:15:00"
        )
        
        if not df.empty:
            print(f"✅ Retrieved {len(df)} bars")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Latest close: {df['close'].iloc[-1]:.2f}")
        else:
            print("❌ No data retrieved")
            
    except Exception as e:
        print(f"❌ Could not get price history: {e}")
    
    try:
        print("\n💰 Getting quote for BTCUSD...")
        
        quote = client.get_quote(symbol="BTCUSD")
        
        if quote:
            print(f"✅ Quote retrieved")
            print(f"   Symbol: {quote.get('symbol', 'N/A')}")
            print(f"   Bid: {quote.get('bid', 'N/A')}")
            print(f"   Ask: {quote.get('ask', 'N/A')}")
        else:
            print("❌ No quote data retrieved")
            
    except Exception as e:
        print(f"❌ Could not get quote: {e}")
    
    try:
        print("\n📝 Placing order for EURUSD...")
        
        order = client.place_order(
            symbol="EURUSD",
            order_type="BUY",
            volume=0.1,
            sl=1.0500,
            tp=1.0600,
            comment="Test order"
        )
        
        if order:
            print(f"✅ Order placed")
            print(f"   Order ID: {order.get('order', 'N/A')}")
            print(f"   Symbol: {order.get('symbol', 'N/A')}")
            print(f"   Type: {order.get('type', 'N/A')}")
            print(f"   Volume: {order.get('volume', 'N/A')}")
        else:
            print("❌ No order response")
            
    except Exception as e:
        print(f"❌ Could not place order: {e}")
    
    print("\n=== Example completed ===")

if __name__ == "__main__":
    main()