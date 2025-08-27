"""
PipEngine Configuration
Centralized configuration for all project paths and settings
"""

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

# File paths
KLINES_CSV = DATA_DIR / "klines.csv"

# Trading settings
DEFAULT_SYMBOL = "OANDA:XAUUSD"
DEFAULT_TIMEFRAME = "M1"
DEFAULT_COMMISSION = 0.001
DEFAULT_POSITION_SIZE = 0.1

# Strategy settings
EMA_PERIOD = 200
WILLIAMS_FRACTAL_LEFT_RANGE = 9
WILLIAMS_FRACTAL_RIGHT_RANGE = 9
BREAKOUT_BODY_THRESHOLD = 0.5  # 50% of body above reference

# Backtest settings
DEFAULT_INITIAL_CAPITAL = 10000
DEFAULT_MAX_ROWS = 500

# Backtest time range settings
DEFAULT_START_DATE = "2025-08-01"
DEFAULT_END_DATE = "2025-08-10"
DEFAULT_TIMEFRAME = "M1"

# Data retrieval settings
DATA_SOURCE = "csv"  # Options: "csv", "api", "database"
DATA_FILE_PATH = "results/data/klines.csv"  # Default CSV path
DATA_BARS = 1000  # Number of bars to fetch
DATA_UPDATE_INTERVAL = 60  # Seconds between data updates



# API settings
META_TRADER_BASE_URL = "http://trade-api.reza-developer.com"
