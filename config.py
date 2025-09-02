import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Data directories
DATA_DIR = PROJECT_ROOT / "results" / "data"
BACKTEST_DIR = PROJECT_ROOT / "results" / "backtests"
LOG_DIR = PROJECT_ROOT / "results" / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# API settings
META_TRADER_BASE_URL = "http://trade-api.reza-developer.com"

# Telegram Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
CHAT_ID = "YOUR_CHAT_ID_HERE"      # Your Telegram chat ID

# Database Configuration
DATABASE_PATH = "telegram_monitoring/orders.db"

# Notification Settings
ENABLE_NOTIFICATIONS = True
NOTIFICATION_TYPES = [
    "ORDER_CREATED",
    "ORDER_CANCELLED", 
    "TAKE_PROFIT",
    "STOP_LOSS"
]

# Bot Settings
BOT_NAME = "PipEngine Trading Bot"
BOT_DESCRIPTION = "Monitors trading orders and sends notifications"

# MongoDB Configuration
MONGODB_CONNECTION_STRING = "mongodb://localhost:27017/"
MONGODB_DATABASE_NAME = "pipengine"
MONGODB_TRADING_COLLECTION = "trading_data"
MONGODB_ORDERS_COLLECTION = "orders"
