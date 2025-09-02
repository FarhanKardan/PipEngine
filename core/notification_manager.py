import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from telegram_monitoring.telegram_bot import TelegramBot
from logger import get_logger

class NotificationManager:
    """Manages Telegram notifications for trading events"""
    
    def __init__(self):
        self.logger = get_logger("NotificationManager")
        self.telegram_bot = TelegramBot()
        
    async def send_startup_notification(self, symbol: str):
        """Send startup notification"""
        message = f"🚀 PipEngine Pipeline Started!\n\nMonitoring {symbol} for trading signals..."
        await self.telegram_bot.send_notification(message, "INFO")
        
    async def send_shutdown_notification(self):
        """Send shutdown notification"""
        message = "🛑 PipEngine Pipeline Stopped"
        await self.telegram_bot.send_notification(message, "INFO")
        
    async def send_position_opened(self, symbol: str, position_data: Dict[str, Any]):
        """Send notification for new position opened"""
        message = f"""
🆕 NEW POSITION OPENED

📊 Symbol: {symbol}
📈 Type: {position_data['type']}
💰 Entry Price: {position_data['entry_price']:.2f}
🎯 Take Profit: {position_data['tp_price']:.2f}
🛑 Stop Loss: {position_data['sl_price']:.2f}
⏰ Time: {position_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.telegram_bot.send_notification(message.strip(), "ORDER_CREATED")
        
    async def send_position_closed(self, symbol: str, position_data: Dict[str, Any]):
        """Send notification for position closed"""
        message = f"""
❌ POSITION CLOSED

📊 Symbol: {symbol}
📈 Type: {position_data['type']}
💰 Entry Price: {position_data['entry_price']:.2f}
💰 Exit Price: {position_data['exit_price']:.2f}
📊 P&L: {position_data['pips']:.1f} pips
⏰ Time: {position_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.telegram_bot.send_notification(message.strip(), "ORDER_CANCELLED")
        
    async def send_take_profit(self, symbol: str, position_data: Dict[str, Any]):
        """Send notification for take profit hit"""
        message = f"""
💰 TAKE PROFIT HIT!

📊 Symbol: {symbol}
📈 Type: {position_data['type']}
💰 Entry Price: {position_data['entry_price']:.2f}
💰 Exit Price: {position_data['exit_price']:.2f}
📊 P&L: +{position_data['pips']:.1f} pips
⏰ Time: {position_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.telegram_bot.send_notification(message.strip(), "TAKE_PROFIT")
        
    async def send_stop_loss(self, symbol: str, position_data: Dict[str, Any]):
        """Send notification for stop loss hit"""
        message = f"""
🛑 STOP LOSS HIT!

📊 Symbol: {symbol}
📈 Type: {position_data['type']}
💰 Entry Price: {position_data['entry_price']:.2f}
💰 Exit Price: {position_data['exit_price']:.2f}
📊 P&L: {position_data['pips']:.1f} pips
⏰ Time: {position_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.telegram_bot.send_notification(message.strip(), "STOP_LOSS")
        
    async def handle_position_event(self, symbol: str, event_data: Dict[str, Any]):
        """Handle different types of position events"""
        try:
            action = event_data.get('action')
            
            if action == 'OPEN':
                await self.send_position_opened(symbol, event_data)
            elif action == 'CLOSE':
                await self.send_position_closed(symbol, event_data)
            elif action == 'TAKE_PROFIT':
                await self.send_take_profit(symbol, event_data)
            elif action == 'STOP_LOSS':
                await self.send_stop_loss(symbol, event_data)
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
