#!/usr/bin/env python3
"""
Test the Telegram bot with MongoDB integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from telegram_monitoring.telegram_bot import TelegramBot, TelegramMonitor
from logger import get_logger

async def test_telegram_mongo():
    """Test Telegram bot with MongoDB integration"""
    logger = get_logger("TelegramMongoTest")
    logger.info("Testing Telegram bot with MongoDB integration...")
    
    # Initialize bot
    bot = TelegramBot()
    
    if not bot.mongo_handler.check_connection():
        logger.error("MongoDB connection failed. Please ensure MongoDB is running.")
        return
    
    logger.info("✅ MongoDB connection successful")
    
    # Test adding an order
    test_order = {
        'order_id': 'TELEGRAM_TEST_001',
        'symbol': 'XAUUSD',
        'order_type': 'BUY',
        'volume': 0.1,
        'price': 2000.0,
        'sl': 1950.0,
        'tp': 2050.0,
        'status': 'ACTIVE'
    }
    
    logger.info("📝 Adding test order...")
    doc_id = bot.add_order(test_order)
    if doc_id:
        logger.info(f"✅ Order added successfully: {doc_id}")
    else:
        logger.error("❌ Failed to add order")
        return
    
    # Test getting active orders
    logger.info("📊 Getting active orders...")
    active_orders = bot.get_active_orders()
    logger.info(f"✅ Found {len(active_orders)} active orders")
    
    # Test sending notification
    logger.info("📢 Testing notification...")
    test_message = "🧪 Test notification from Telegram bot with MongoDB integration!"
    result = await bot.send_notification(test_message, "INFO")
    
    if result:
        logger.info("✅ Notification sent successfully!")
        print("✅ Telegram notification test passed!")
    else:
        logger.error("❌ Notification failed!")
        print("❌ Telegram notification test failed!")
    
    # Test order update
    logger.info("🔄 Testing order update...")
    success = bot.update_order('TELEGRAM_TEST_001', {'status': 'CLOSED', 'profit': 25.0})
    if success:
        logger.info("✅ Order updated successfully!")
    else:
        logger.error("❌ Order update failed!")
    
    # Test 24-hour report
    logger.info("📈 Testing 24-hour report...")
    report = bot.mongo_handler.get_last_24h_orders_report()
    if report:
        logger.info(f"✅ Report generated: {report['total_orders']} orders found")
        print(f"📊 24h Report: {report['total_orders']} orders, {report['total_profit']} profit")
    else:
        logger.error("❌ Report generation failed!")
    
    # Close connection
    bot.mongo_handler.close_connection()
    logger.info("🔌 MongoDB connection closed")

def main():
    """Main test function"""
    print("🧪 Testing Telegram Bot with MongoDB Integration")
    print("=" * 60)
    
    try:
        asyncio.run(test_telegram_mongo())
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
