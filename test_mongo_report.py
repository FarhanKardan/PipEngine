#!/usr/bin/env python3
"""
Test the MongoDB 24-hour report functionality
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from mongo_handler.mongo_client import MongoHandler
from datetime import datetime, timedelta

def test_mongo_report():
    """Test the 24-hour report functionality"""
    print("🍃 Testing MongoDB 24-Hour Report")
    print("=" * 50)
    
    # Initialize handler
    handler = MongoHandler()
    
    if not handler.check_connection():
        print("❌ Failed to connect to MongoDB")
        print("Make sure MongoDB is running on localhost:27017")
        return
    
    print("✅ Connected to MongoDB")
    
    # Add some test orders with different timestamps
    test_orders = [
        {
            'order_id': 'TEST_001',
            'symbol': 'XAUUSD',
            'order_type': 'BUY',
            'volume': 0.1,
            'price': 2000.0,
            'status': 'ACTIVE',
            'timestamp': datetime.now()  # Current time
        },
        {
            'order_id': 'TEST_002',
            'symbol': 'EURUSD',
            'order_type': 'SELL',
            'volume': 0.2,
            'price': 1.0850,
            'status': 'CLOSED',
            'profit': 15.50,
            'timestamp': datetime.now() - timedelta(hours=2)  # 2 hours ago
        },
        {
            'order_id': 'TEST_003',
            'symbol': 'XAUUSD',
            'order_type': 'BUY',
            'volume': 0.15,
            'price': 2010.0,
            'status': 'CLOSED_TP',
            'profit': 25.75,
            'timestamp': datetime.now() - timedelta(hours=12)  # 12 hours ago
        },
        {
            'order_id': 'TEST_004',
            'symbol': 'GBPUSD',
            'order_type': 'SELL',
            'volume': 0.05,
            'price': 1.2650,
            'status': 'CANCELLED',
            'timestamp': datetime.now() - timedelta(hours=6)  # 6 hours ago
        }
    ]
    
    # Add test orders
    print("\n📝 Adding test orders...")
    for order in test_orders:
        doc_id = handler.add_record(order)
        if doc_id:
            print(f"✅ Added {order['order_id']} - {order['symbol']} {order['order_type']}")
    
    # Generate 24-hour report
    print("\n📈 24-Hour Trading Report:")
    print("-" * 50)
    report = handler.get_last_24h_orders_report()
    
    if report:
        if report['total_orders'] == 0:
            print(f"📊 {report['message']}")
        else:
            print(f"📊 Period: {report['period']}")
            print(f"📊 Total Orders: {report['total_orders']}")
            print(f"📊 Buy Orders: {report['order_types']['buy_orders']}")
            print(f"📊 Sell Orders: {report['order_types']['sell_orders']}")
            print(f"📊 Active: {report['order_status']['active']}")
            print(f"📊 Closed: {report['order_status']['closed']}")
            print(f"📊 Cancelled: {report['order_status']['cancelled']}")
            print(f"📊 Symbols: {', '.join(report['symbols_traded'])}")
            print(f"📊 Total Volume: {report['total_volume']}")
            print(f"📊 Average Price: {report['average_price']}")
            print(f"📊 Total Profit: {report['total_profit']}")
            print(f"📊 Report Generated: {report['timestamp']}")
    else:
        print("❌ Failed to generate report")
    
    # Close connection
    handler.close_connection()
    print("\n🔌 Connection closed")

if __name__ == "__main__":
    test_mongo_report()
