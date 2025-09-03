#!/usr/bin/env python3
"""
Simple Telegram notification without complex bot setup
"""

import requests
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from config import BOT_TOKEN, CHAT_ID
from logger import get_logger

class SimpleTelegram:
    
    def __init__(self):
        self.logger = get_logger("SimpleTelegram")
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message):
        """Send a simple message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False

def test_telegram():
    """Test the simple Telegram function"""
    telegram = SimpleTelegram()
    
    message = """
🟢 **POSITION OPENED**

**Action:** BUY
**Symbol:** XAUUSD
**Time:** 2025-09-03 12:06:00
**Price:** 2000.00
**EMA:** 1995.50
**Strategy:** EMA Fractal

Test notification from pipeline.
    """.strip()
    
    print("Sending test Telegram message...")
    success = telegram.send_message(message)
    
    if success:
        print("✅ Telegram message sent successfully!")
    else:
        print("❌ Failed to send Telegram message")

if __name__ == "__main__":
    test_telegram()
