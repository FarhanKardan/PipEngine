#!/usr/bin/env python3
"""
Test multiple chat IDs
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from telegram_monitoring.telegram_bot import TelegramBot

async def test_multiple_chats():
    """Test sending to multiple chat IDs"""
    bot = TelegramBot()
    
    message = "Test message to multiple chat IDs - both should receive this!"
    result = await bot.send_notification(message, "INFO")
    
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_multiple_chats())
