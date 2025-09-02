import asyncio
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from telegram_bot import TelegramBot
from config import BOT_TOKEN, CHAT_ID, DATABASE_PATH

class OrderMonitor:
    
    def __init__(self, bot_token: str = None, chat_id: str = None, db_path: str = None):
        self.logger = get_logger("OrderMonitor")
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        self.db_path = db_path or DATABASE_PATH
        self.bot = None
        self.is_running = False
        
        if self.bot_token != "YOUR_BOT_TOKEN_HERE":
            self.bot = TelegramBot(self.bot_token, self.chat_id, self.db_path)
            self.logger.info("Order monitor initialized with Telegram bot")
        else:
            self.logger.warning("Order monitor initialized without Telegram bot - check config")
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT order_id, symbol, order_type, volume, price, sl, tp, created_at
                FROM orders 
                WHERE status = 'ACTIVE'
                ORDER BY created_at DESC
            ''')
            
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    'order_id': row[0],
                    'symbol': row[1],
                    'order_type': row[2],
                    'volume': row[3],
                    'price': row[4],
                    'sl': row[5],
                    'tp': row[6],
                    'created_at': row[7]
                })
            
            conn.close()
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get active orders: {e}")
            return []
    
    def check_order_status(self, order: Dict, current_price: float) -> str:
        """Check if order hit TP or SL levels"""
        order_type = order['order_type']
        entry_price = order['price']
        sl = order['sl']
        tp = order['tp']
        
        if order_type == 'BUY':
            if current_price >= tp:
                return 'TP_HIT'
            elif current_price <= sl:
                return 'SL_HIT'
        else:  # SELL
            if current_price <= tp:
                return 'TP_HIT'
            elif current_price >= sl:
                return 'SL_HIT'
        
        return 'ACTIVE'
    
    def calculate_pnl(self, order: Dict, exit_price: float) -> float:
        """Calculate profit/loss for order"""
        order_type = order['order_type']
        entry_price = order['price']
        volume = order['volume']
        
        if order_type == 'BUY':
            return (exit_price - entry_price) * volume
        else:  # SELL
            return (entry_price - exit_price) * volume
    
    async def send_status_update(self, active_orders: List[Dict]):
        """Send status update to Telegram"""
        if not self.bot or not active_orders:
            return
        
        try:
            message = f"📊 Order Status Update\n\n"
            message += f"Active Orders: {len(active_orders)}\n"
            message += f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            for order in active_orders[:5]:  # Show max 5 orders
                message += (
                    f"🆔 {order['order_id']}\n"
                    f"📈 {order['symbol']} {order['order_type']}\n"
                    f"💰 Entry: {order['price']}\n"
                    f"🛑 SL: {order['sl']}\n"
                    f"🎯 TP: {order['tp']}\n\n"
                )
            
            if len(active_orders) > 5:
                message += f"... and {len(active_orders) - 5} more orders"
            
            await self.bot.send_notification(message, "INFO")
            
        except Exception as e:
            self.logger.error(f"Failed to send status update: {e}")
    
    async def monitor_orders(self, check_interval: int = 60):
        """Monitor orders every specified interval (seconds)"""
        self.logger.info(f"Starting order monitoring every {check_interval} seconds")
        self.is_running = True
        
        while self.is_running:
            try:
                active_orders = self.get_active_orders()
                
                if active_orders:
                    self.logger.info(f"Monitoring {len(active_orders)} active orders")
                    
                    # Send status update every 5 minutes (300 seconds)
                    if int(time.time()) % 300 == 0:
                        await self.send_status_update(active_orders)
                    
                    # Here you would check current prices and update order status
                    # For now, just log the active orders
                    for order in active_orders:
                        self.logger.debug(f"Active order: {order['order_id']} - {order['symbol']} {order['order_type']}")
                else:
                    self.logger.info("No active orders to monitor")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error during order monitoring: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.logger.info("Stopping order monitoring")
        self.is_running = False
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if self.bot:
            await self.bot.start_bot()
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.bot:
            await self.bot.stop_bot()

class SimpleOrderMonitor:
    """Simplified order monitor for basic status checking"""
    
    def __init__(self):
        self.logger = get_logger("SimpleOrderMonitor")
        self.monitor = OrderMonitor()
        self.logger.info("Simple order monitor initialized")
    
    async def run_monitoring(self, duration_minutes: int = 10):
        """Run monitoring for specified duration"""
        self.logger.info(f"Starting simple order monitoring for {duration_minutes} minutes")
        
        try:
            # Start bot
            await self.monitor.start_bot()
            
            # Start monitoring in background
            monitor_task = asyncio.create_task(self.monitor.monitor_orders(60))  # Check every 60 seconds
            
            # Run for specified duration
            await asyncio.sleep(duration_minutes * 60)
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            monitor_task.cancel()
            
            self.logger.info("Simple order monitoring completed")
            
        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
        
        finally:
            await self.monitor.stop_bot()

async def main():
    """Main function for testing order monitoring"""
    print("🔍 Order Status Monitor")
    print("=" * 40)
    print("This will check order status every 1 minute")
    print("=" * 40)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please configure BOT_TOKEN and CHAT_ID in config.py")
        return
    
    # Create and run simple monitor
    monitor = SimpleOrderMonitor()
    await monitor.run_monitoring(duration_minutes=5)  # Run for 5 minutes

if __name__ == "__main__":
    asyncio.run(main())
