import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from config import BOT_TOKEN, CHAT_ID, CHAT_IDS, DATABASE_PATH

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Create dummy classes for when telegram is not available
    class Update:
        pass
    class ContextTypes:
        class DEFAULT_TYPE:
            pass

class TelegramBot:
    
    def __init__(self, bot_token: str = None, chat_id: str = None, chat_ids: list = None, db_path: str = None):
        self.logger = get_logger("TelegramBot")
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        self.chat_ids = chat_ids or CHAT_IDS
        self.db_path = db_path or DATABASE_PATH
        
        if not TELEGRAM_AVAILABLE:
            self.logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            return
        
        self.bot = Bot(token=self.bot_token)
        self.application = None
        self._init_database()
        
        self.logger.info("Telegram bot initialized")
    
    def _init_database(self):
        """Initialize SQLite database for order tracking"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE,
                    symbol TEXT,
                    order_type TEXT,
                    volume REAL,
                    price REAL,
                    sl REAL,
                    tp REAL,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    telegram_sent BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    notification_type TEXT,
                    message TEXT,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            self.logger.error("Cannot start bot: python-telegram-bot not available")
            return
        
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("status", self._status_command))
            self.application.add_handler(CommandHandler("orders", self._orders_command))
            
            self.logger.info("Starting Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Telegram bot stopped")
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 PipEngine Trading Bot\n\n"
            "Available commands:\n"
            "/status - Check bot status\n"
            "/orders - View recent orders\n\n"
            "I will notify you about:\n"
            "• New orders created\n"
            "• Orders cancelled\n"
            "• Take Profit hit\n"
            "• Stop Loss hit"
        )
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'ACTIVE'")
            active_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE sent_at >= datetime('now', '-24 hours')")
            recent_notifications = cursor.fetchone()[0]
            
            conn.close()
            
            status_message = (
                f"📊 Bot Status\n\n"
                f"Total Orders: {total_orders}\n"
                f"Active Orders: {active_orders}\n"
                f"Notifications (24h): {recent_notifications}\n\n"
                f"Status: ✅ Online"
            )
            
            await update.message.reply_text(status_message)
            
        except Exception as e:
            self.logger.error(f"Status command failed: {e}")
            await update.message.reply_text("❌ Error retrieving status")
    
    async def _orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT order_id, symbol, order_type, volume, price, status, created_at
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            orders = cursor.fetchall()
            conn.close()
            
            if not orders:
                await update.message.reply_text("📋 No orders found")
                return
            
            message = "📋 Recent Orders\n\n"
            for order in orders:
                order_id, symbol, order_type, volume, price, status, created_at = order
                message += (
                    f"🆔 {order_id}\n"
                    f"📈 {symbol} {order_type}\n"
                    f"📊 {volume} @ {price}\n"
                    f"📊 Status: {status}\n"
                    f"🕐 {created_at}\n\n"
                )
            
            await update.message.reply_text(message)
            
        except Exception as e:
            self.logger.error(f"Orders command failed: {e}")
            await update.message.reply_text("❌ Error retrieving orders")
    
    def add_order(self, order_data: Dict):
        """Add new order to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO orders 
                (order_id, symbol, order_type, volume, price, sl, tp, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data.get('order_id'),
                order_data.get('symbol'),
                order_data.get('order_type'),
                order_data.get('volume'),
                order_data.get('price'),
                order_data.get('sl'),
                order_data.get('tp'),
                order_data.get('status', 'ACTIVE'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Order added to database: {order_data.get('order_id')}")
            
        except Exception as e:
            self.logger.error(f"Failed to add order: {e}")
    
    def update_order(self, order_id: str, updates: Dict):
        """Update existing order"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [order_id]
            
            cursor.execute(f'''
                UPDATE orders 
                SET {set_clause}, updated_at = ?
                WHERE order_id = ?
            ''', values + [datetime.now().isoformat()])
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Order updated: {order_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update order: {e}")
    
    async def send_notification(self, message: str, notification_type: str = "INFO"):
        """Send notification to all configured Telegram chat IDs"""
        if not TELEGRAM_AVAILABLE:
            self.logger.warning("Telegram not available, notification not sent")
            return False
        
        try:
            emoji_map = {
                "ORDER_CREATED": "🆕",
                "ORDER_CANCELLED": "❌",
                "TAKE_PROFIT": "💰",
                "STOP_LOSS": "🛑",
                "INFO": "ℹ️",
                "ERROR": "⚠️"
            }
            
            emoji = emoji_map.get(notification_type, "📢")
            formatted_message = f"{emoji} {message}"
            
            success_count = 0
            total_chats = len(self.chat_ids)
            
            # Send to all chat IDs
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=formatted_message)
                    success_count += 1
                    self.logger.info(f"Notification sent to chat {chat_id}: {notification_type}")
                except Exception as chat_error:
                    self.logger.error(f"Failed to send to chat {chat_id}: {chat_error}")
            
            if success_count > 0:
                self.logger.info(f"Notification sent to {success_count}/{total_chats} chats: {notification_type}")
                return True
            else:
                self.logger.error(f"Failed to send notification to any chat")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    async def notify_order_created(self, order_data: Dict):
        """Send order created notification"""
        message = (
            f"New Order Created\n\n"
            f"🆔 Order ID: {order_data.get('order_id')}\n"
            f"📈 Symbol: {order_data.get('symbol')}\n"
            f"📊 Type: {order_data.get('order_type')}\n"
            f"📊 Volume: {order_data.get('volume')}\n"
            f"💰 Price: {order_data.get('price')}\n"
            f"🛑 SL: {order_data.get('sl', 'None')}\n"
            f"🎯 TP: {order_data.get('tp', 'None')}"
        )
        
        await self.send_notification(message, "ORDER_CREATED")
    
    async def notify_order_cancelled(self, order_id: str, reason: str = ""):
        """Send order cancelled notification"""
        message = f"Order Cancelled\n\n🆔 Order ID: {order_id}"
        if reason:
            message += f"\n📝 Reason: {reason}"
        
        await self.send_notification(message, "ORDER_CANCELLED")
    
    async def notify_take_profit(self, order_id: str, symbol: str, price: float, profit: float):
        """Send take profit hit notification"""
        message = (
            f"Take Profit Hit! 💰\n\n"
            f"🆔 Order ID: {order_id}\n"
            f"📈 Symbol: {symbol}\n"
            f"💰 Exit Price: {price}\n"
            f"💵 Profit: {profit:.2f}"
        )
        
        await self.send_notification(message, "TAKE_PROFIT")
    
    async def notify_stop_loss(self, order_id: str, symbol: str, price: float, loss: float):
        """Send stop loss hit notification"""
        message = (
            f"Stop Loss Hit! 🛑\n\n"
            f"🆔 Order ID: {order_id}\n"
            f"📈 Symbol: {symbol}\n"
            f"💰 Exit Price: {price}\n"
            f"💸 Loss: {loss:.2f}"
        )
        
        await self.send_notification(message, "STOP_LOSS")
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders"""
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

class TelegramMonitor:
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.logger = get_logger("TelegramMonitor")
        self.bot = TelegramBot(bot_token, chat_id)
        self.logger.info("Telegram monitor initialized")
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        self.logger.info("Starting Telegram monitoring")
        await self.bot.start_bot()
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.logger.info("Stopping Telegram monitoring")
        await self.bot.stop_bot()
    
    def track_order(self, order_data: Dict):
        """Track a new order"""
        self.bot.add_order(order_data)
        asyncio.create_task(self.bot.notify_order_created(order_data))
    
    def track_order_cancelled(self, order_id: str, reason: str = ""):
        """Track order cancellation"""
        self.bot.update_order(order_id, {'status': 'CANCELLED'})
        asyncio.create_task(self.bot.notify_order_cancelled(order_id, reason))
    
    def track_take_profit(self, order_id: str, symbol: str, price: float, profit: float):
        """Track take profit hit"""
        self.bot.update_order(order_id, {'status': 'CLOSED_TP'})
        asyncio.create_task(self.bot.notify_take_profit(order_id, symbol, price, profit))
    
    def track_stop_loss(self, order_id: str, symbol: str, price: float, loss: float):
        """Track stop loss hit"""
        self.bot.update_order(order_id, {'status': 'CLOSED_SL'})
        asyncio.create_task(self.bot.notify_stop_loss(order_id, symbol, price, loss))

# Example usage
async def main():
    """Example usage of the Telegram bot"""
    monitor = TelegramMonitor()
    
    try:
        await monitor.start_monitoring()
        
        # Example: Track a new order
        order_data = {
            'order_id': '12345',
            'symbol': 'XAUUSD',
            'order_type': 'BUY',
            'volume': 0.1,
            'price': 2000.0,
            'sl': 1950.0,
            'tp': 2050.0,
            'status': 'ACTIVE'
        }
        
        monitor.track_order(order_data)
        
        # Keep running
        await asyncio.sleep(3600)  # Run for 1 hour
        
    except KeyboardInterrupt:
        print("Stopping bot...")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
