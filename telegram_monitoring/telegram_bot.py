
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from config import BOT_TOKEN, CHAT_ID, CHAT_IDS
from mongo_handler.mongo_client import MongoHandler

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
    
    def __init__(self, bot_token: str = None, chat_id: str = None, chat_ids: list = None):
        self.logger = get_logger("TelegramBot")
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        self.chat_ids = chat_ids or CHAT_IDS
        
        if not TELEGRAM_AVAILABLE:
            self.logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            return
        
        self.bot = Bot(token=self.bot_token)
        self.application = None
        self.mongo_handler = MongoHandler()
        
        self.logger.info("Telegram bot initialized")
    

    
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
        
        # Close MongoDB connection
        if hasattr(self, 'mongo_handler'):
            self.mongo_handler.close_connection()
    
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
            if not self.mongo_handler.check_connection():
                await update.message.reply_text("❌ Database connection failed")
                return
            
            # Get 24-hour report
            report = self.mongo_handler.get_last_24h_orders_report()
            
            if report and report['total_orders'] > 0:
                status_message = (
                    f"📊 Bot Status\n\n"
                    f"Total Orders (24h): {report['total_orders']}\n"
                    f"Active Orders: {report['order_status']['active']}\n"
                    f"Closed Orders: {report['order_status']['closed']}\n"
                    f"Cancelled Orders: {report['order_status']['cancelled']}\n"
                    f"Total Profit: {report['total_profit']}\n\n"
                    f"Status: ✅ Online"
                )
            else:
                status_message = (
                    f"📊 Bot Status\n\n"
                    f"Total Orders (24h): 0\n"
                    f"Active Orders: 0\n"
                    f"Status: ✅ Online"
                )
            
            await update.message.reply_text(status_message)
            
        except Exception as e:
            self.logger.error(f"Status command failed: {e}")
            await update.message.reply_text("❌ Error retrieving status")
    
    async def _orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command"""
        try:
            if not self.mongo_handler.check_connection():
                await update.message.reply_text("❌ Database connection failed")
                return
            
            # Get active orders
            active_orders = self.mongo_handler.get_active_orders()
            
            if not active_orders:
                await update.message.reply_text("📋 No active orders found")
                return
            
            message = "📋 Active Orders\n\n"
            for order in active_orders[:10]:  # Limit to 10 orders
                message += (
                    f"🆔 {order.get('order_id', 'N/A')}\n"
                    f"📈 {order.get('symbol', 'N/A')} {order.get('order_type', 'N/A')}\n"
                    f"📊 {order.get('volume', 0)} @ {order.get('price', 0)}\n"
                    f"📊 Status: {order.get('status', 'N/A')}\n"
                    f"🕐 {order.get('timestamp', 'N/A')}\n\n"
                )
            
            await update.message.reply_text(message)
            
        except Exception as e:
            self.logger.error(f"Orders command failed: {e}")
            await update.message.reply_text("❌ Error retrieving orders")
    
    def add_order(self, order_data: Dict):
        """Add new order to database"""
        try:
            doc_id = self.mongo_handler.add_order(order_data)
            if doc_id:
                self.logger.info(f"Order added to database: {order_data.get('order_id')}")
                return doc_id
            else:
                self.logger.error(f"Failed to add order: {order_data.get('order_id')}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to add order: {e}")
            return None
    
    def update_order(self, order_id: str, updates: Dict):
        """Update existing order"""
        try:
            success = self.mongo_handler.update_order_status(order_id, updates.get('status', 'ACTIVE'), updates)
            if success:
                self.logger.info(f"Order updated: {order_id}")
                return True
            else:
                self.logger.error(f"Failed to update order: {order_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update order: {e}")
            return False
    
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
            return self.mongo_handler.get_active_orders()
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
        self.bot.mongo_handler.cancel_order(order_id, reason)
        asyncio.create_task(self.bot.notify_order_cancelled(order_id, reason))
    
    def track_take_profit(self, order_id: str, symbol: str, price: float, profit: float):
        """Track take profit hit"""
        self.bot.mongo_handler.close_order(order_id, price, profit)
        asyncio.create_task(self.bot.notify_take_profit(order_id, symbol, price, profit))
    
    def track_stop_loss(self, order_id: str, symbol: str, price: float, loss: float):
        """Track stop loss hit"""
        self.bot.mongo_handler.close_order(order_id, price, loss)
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
