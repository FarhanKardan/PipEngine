import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from telegram_bot import TelegramMonitor
from config import BOT_TOKEN, CHAT_ID, ENABLE_NOTIFICATIONS

class OrderTracker:
    
    def __init__(self):
        self.logger = get_logger("OrderTracker")
        self.telegram_monitor = None
        
        if ENABLE_NOTIFICATIONS and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            self.telegram_monitor = TelegramMonitor(BOT_TOKEN, CHAT_ID)
            self.logger.info("Telegram monitoring enabled")
        else:
            self.logger.warning("Telegram monitoring disabled - check config.py")
    
    async def start_tracking(self):
        """Start the order tracking system"""
        if self.telegram_monitor:
            await self.telegram_monitor.start_monitoring()
            self.logger.info("Order tracking started")
    
    async def stop_tracking(self):
        """Stop the order tracking system"""
        if self.telegram_monitor:
            await self.telegram_monitor.stop_monitoring()
            self.logger.info("Order tracking stopped")
    
    def track_new_order(self, order_data: Dict):
        """Track a new order creation"""
        self.logger.info(f"Tracking new order: {order_data.get('order_id')}")
        
        if self.telegram_monitor:
            self.telegram_monitor.track_order(order_data)
        else:
            self.logger.info(f"Order created: {order_data}")
    
    def track_order_cancelled(self, order_id: str, reason: str = ""):
        """Track order cancellation"""
        self.logger.info(f"Tracking order cancellation: {order_id}")
        
        if self.telegram_monitor:
            self.telegram_monitor.track_order_cancelled(order_id, reason)
        else:
            self.logger.info(f"Order cancelled: {order_id} - {reason}")
    
    def track_take_profit(self, order_id: str, symbol: str, price: float, profit: float):
        """Track take profit hit"""
        self.logger.info(f"Tracking take profit: {order_id} - Profit: {profit}")
        
        if self.telegram_monitor:
            self.telegram_monitor.track_take_profit(order_id, symbol, price, profit)
        else:
            self.logger.info(f"Take profit hit: {order_id} - {symbol} @ {price} - Profit: {profit}")
    
    def track_stop_loss(self, order_id: str, symbol: str, price: float, loss: float):
        """Track stop loss hit"""
        self.logger.info(f"Tracking stop loss: {order_id} - Loss: {loss}")
        
        if self.telegram_monitor:
            self.telegram_monitor.track_stop_loss(order_id, symbol, price, loss)
        else:
            self.logger.info(f"Stop loss hit: {order_id} - {symbol} @ {price} - Loss: {loss}")
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders"""
        if self.telegram_monitor:
            return self.telegram_monitor.bot.get_active_orders()
        else:
            self.logger.warning("Telegram monitor not available")
            return []

class MockTradingSystem:
    """Mock trading system for testing notifications"""
    
    def __init__(self, order_tracker: OrderTracker):
        self.logger = get_logger("MockTradingSystem")
        self.order_tracker = order_tracker
        self.orders = {}
        self.order_counter = 0
    
    def create_order(self, symbol: str, order_type: str, volume: float, 
                    price: float, sl: Optional[float] = None, tp: Optional[float] = None):
        """Create a mock order"""
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:04d}"
        
        order_data = {
            'order_id': order_id,
            'symbol': symbol,
            'order_type': order_type,
            'volume': volume,
            'price': price,
            'sl': sl,
            'tp': tp,
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat()
        }
        
        self.orders[order_id] = order_data
        self.order_tracker.track_new_order(order_data)
        
        self.logger.info(f"Mock order created: {order_id}")
        return order_id
    
    def cancel_order(self, order_id: str, reason: str = "Manual cancellation"):
        """Cancel a mock order"""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'CANCELLED'
            self.order_tracker.track_order_cancelled(order_id, reason)
            self.logger.info(f"Mock order cancelled: {order_id}")
        else:
            self.logger.warning(f"Order not found: {order_id}")
    
    def hit_take_profit(self, order_id: str, exit_price: float):
        """Simulate take profit hit"""
        if order_id in self.orders:
            order = self.orders[order_id]
            entry_price = order['price']
            volume = order['volume']
            profit = (exit_price - entry_price) * volume
            
            self.orders[order_id]['status'] = 'CLOSED_TP'
            self.order_tracker.track_take_profit(order_id, order['symbol'], exit_price, profit)
            self.logger.info(f"Mock take profit hit: {order_id}")
        else:
            self.logger.warning(f"Order not found: {order_id}")
    
    def hit_stop_loss(self, order_id: str, exit_price: float):
        """Simulate stop loss hit"""
        if order_id in self.orders:
            order = self.orders[order_id]
            entry_price = order['price']
            volume = order['volume']
            loss = abs(exit_price - entry_price) * volume
            
            self.orders[order_id]['status'] = 'CLOSED_SL'
            self.order_tracker.track_stop_loss(order_id, order['symbol'], exit_price, loss)
            self.logger.info(f"Mock stop loss hit: {order_id}")
        else:
            self.logger.warning(f"Order not found: {order_id}")

async def test_notifications():
    """Test the notification system"""
    logger = get_logger("TestNotifications")
    
    logger.info("Starting notification test")
    
    # Initialize order tracker
    order_tracker = OrderTracker()
    await order_tracker.start_tracking()
    
    # Initialize mock trading system
    mock_system = MockTradingSystem(order_tracker)
    
    try:
        # Test 1: Create orders
        logger.info("Test 1: Creating orders")
        order1 = mock_system.create_order("XAUUSD", "BUY", 0.1, 2000.0, 1950.0, 2050.0)
        order2 = mock_system.create_order("EURUSD", "SELL", 0.2, 1.0500, 1.0600, 1.0400)
        
        await asyncio.sleep(2)
        
        # Test 2: Cancel an order
        logger.info("Test 2: Cancelling order")
        mock_system.cancel_order(order2, "Strategy exit signal")
        
        await asyncio.sleep(2)
        
        # Test 3: Hit take profit
        logger.info("Test 3: Take profit hit")
        mock_system.hit_take_profit(order1, 2050.0)
        
        await asyncio.sleep(2)
        
        # Test 4: Create another order and hit stop loss
        logger.info("Test 4: Stop loss hit")
        order3 = mock_system.create_order("GBPUSD", "BUY", 0.15, 1.2500, 1.2400, 1.2600)
        await asyncio.sleep(1)
        mock_system.hit_stop_loss(order3, 1.2400)
        
        await asyncio.sleep(2)
        
        logger.info("Notification test completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    
    finally:
        await order_tracker.stop_tracking()

def main():
    """Main function for testing"""
    print("🤖 Telegram Monitoring System")
    print("=" * 40)
    print("1. Make sure to configure BOT_TOKEN and CHAT_ID in config.py")
    print("2. Install python-telegram-bot: pip install python-telegram-bot")
    print("3. Run this script to test notifications")
    print("=" * 40)
    
    # Run the test
    asyncio.run(test_notifications())

if __name__ == "__main__":
    main()
