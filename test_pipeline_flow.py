#!/usr/bin/env python3
"""
Test Pipeline Flow
Fetches XAUUSD data, saves to CSV, and tests EMA Fractal strategy iteration
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from data_feeder.data_feeder import DataFeeder
from strategies.strategy_1.ema_fractal_strategy import add_ema, calculate_strategy_positions
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops
from telegram_monitoring.telegram_bot import TelegramBot
import asyncio
from logger import get_logger

class TestPipelineFlow:
    
    def __init__(self):
        self.logger = get_logger("TestPipelineFlow")
        self.data_feeder = DataFeeder()
        self.csv_file = "test_data_xauusd_5min.csv"
        self.telegram_bot = TelegramBot()
    
    def send_position_notification(self, signal_type, timestamp, price, ema_value):
        """Send notification when a position opens"""
        try:
            emoji = "🟢" if signal_type == 1 else "🔴"
            action = "BUY" if signal_type == 1 else "SELL"
            
            message = f"""
{emoji} **POSITION OPENED**

**Action:** {action}
**Symbol:** XAUUSD
**Time:** {timestamp}
**Price:** {price:.2f}
**EMA:** {ema_value:.2f}
**Strategy:** EMA Fractal

Position opened by test pipeline.
            """.strip()
            
            # Send to Telegram using the working bot
            try:
                asyncio.run(self.telegram_bot.send_notification(message, "INFO"))
                self.logger.info(f"Telegram notification sent for {action} position")
                print(f"\n📢 NOTIFICATION: {action} position opened!")
                print(f"   Time: {timestamp}")
                print(f"   Price: {price:.2f}")
                print(f"   EMA: {ema_value:.2f}")
                print(f"   ✅ Telegram notification sent!")
            except Exception as telegram_error:
                self.logger.error(f"Telegram failed: {telegram_error}")
                print(f"\n📢 NOTIFICATION: {action} position opened!")
                print(f"   Time: {timestamp}")
                print(f"   Price: {price:.2f}")
                print(f"   EMA: {ema_value:.2f}")
                print(f"   ❌ Telegram notification failed")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
        
    def fetch_and_save_data(self):
        """Fetch XAUUSD data and save to CSV"""
        self.logger.info("Fetching XAUUSD data from Aug 8 to Aug 11 (5-minute timeframe)")
        
        try:
            # Fetch data from Aug 8 to end of Aug 11 (available data range)
            from datetime import datetime, timedelta
            start_date = datetime(2025, 8, 8)  # August 8, 2025
            end_date = datetime(2025, 8, 11, 23, 59, 59)  # End of August 11, 2025
            
            # First, get raw data without date filtering to see what's available
            df = self.data_feeder.fetch_data(
                symbol='XAUUSD',
                interval_minutes=5,  # 5-minute timeframe
                n_bars=5000  # Fetch more bars to ensure we get the date range
            )
            
            if df is None or df.empty:
                self.logger.error("No data received from feeder")
                return None
            
            # Debug: Check what date range we actually got
            self.logger.info(f"Raw data date range: {df.index.min()} to {df.index.max()}")
            self.logger.info(f"Requested date range: {start_date} to {end_date}")
            
            # Manually filter the data to the requested date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            self.logger.info(f"After filtering: {len(df)} bars from {df.index.min()} to {df.index.max()}")
            
            # Save to CSV
            df.to_csv(self.csv_file)
            self.logger.info(f"Data saved to {self.csv_file}")
            self.logger.info(f"Total candles: {len(df)}")
            self.logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch data: {e}")
            return None
    
    def load_data_from_csv(self):
        """Load data from CSV file"""
        try:
            if not os.path.exists(self.csv_file):
                self.logger.error(f"CSV file {self.csv_file} not found")
                return None
            
            df = pd.read_csv(self.csv_file, index_col=0, parse_dates=True)
            self.logger.info(f"Loaded {len(df)} candles from CSV")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return None
    
    def process_single_candle(self, df, current_index):
        """Process a single candle and generate signal using EMA Fractal strategy"""
        try:
            # Get data up to current candle (for indicators calculation)
            current_df = df.iloc[:current_index + 1].copy()
            
            # Need at least 200 candles for EMA calculation
            if len(current_df) < 200:
                return None
            
            # Add EMA
            current_df, ema_col = add_ema(current_df, period=200, price_col='close')
            
            # Calculate Williams Fractal Trailing Stops
            wft_df = williams_fractal_trailing_stops(current_df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close")
            current_df = current_df.join(wft_df)
            
            # Calculate strategy positions
            positions = calculate_strategy_positions(current_df, ema_col)
            
            # Get the latest position
            if len(positions) > 0:
                latest_position = positions.iloc[-1]
                if latest_position != 0:  # Only return non-neutral positions
                    return {
                        'signal': latest_position,
                        'timestamp': current_df.index[-1],
                        'price': current_df['close'].iloc[-1],
                        'ema': current_df[ema_col].iloc[-1]
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing candle {current_index}: {e}")
            return None
    
    def iterate_through_candles(self, df):
        """Iterate through all candles and test strategy"""
        self.logger.info("Starting candle iteration and signal detection")
        
        total_candles = len(df)
        previous_signal = None  # Track previous signal to detect changes
        
        print(f"\n🕯️  Processing {total_candles} candles...")
        print("=" * 60)
        
        for i in range(200, total_candles):  # Start from 200 for EMA calculation
            # Process candle
            signal = self.process_single_candle(df, i)
            
            if signal and signal['signal'] != 0:  # Only show BUY/SELL signals
                current_signal = signal['signal']
                
                # Only print if signal changed
                if previous_signal != current_signal:
                    signal_type = "🟢 BUY" if current_signal == 1 else "🔴 SELL"
                    print(f"{signal['timestamp']} | {signal_type}")
                    
                    # Send Telegram notification for position opening
                    self.send_position_notification(
                        signal_type=current_signal,
                        timestamp=signal['timestamp'],
                        price=signal['price'],
                        ema_value=signal['ema']
                    )
                    
                    previous_signal = current_signal
            
            # Progress indicator every 100 candles
            if i % 100 == 0:
                progress = (i / total_candles) * 100
                print(f"Progress: {progress:.1f}% ({i}/{total_candles} candles processed)")
    
    def run_test(self):
        """Run the complete test pipeline"""
        print("🚀 Test Pipeline Flow - XAUUSD EMA Fractal Strategy")
        print("=" * 60)
        
        # Step 1: Fetch and save data
        print("\n📊 Step 1: Fetching XAUUSD data...")
        df = self.fetch_and_save_data()
        
        if df is None:
            print("❌ Failed to fetch data")
            return
        
        print(f"✅ Data fetched: {len(df)} candles")
        
        # Step 2: Load data from CSV
        print("\n📁 Step 2: Loading data from CSV...")
        df = self.load_data_from_csv()
        
        if df is None:
            print("❌ Failed to load CSV data")
            return
        
        print(f"✅ Data loaded: {len(df)} candles")
        print(f"📅 Date range: {df.index.min()} to {df.index.max()}")
        
        # Step 3: Iterate through candles
        print("\n🔄 Step 3: Testing EMA Fractal strategy...")
        self.iterate_through_candles(df)
        
        print(f"\n💾 Data saved to: {self.csv_file}")
        print("✅ Test pipeline completed!")

def main():
    """Main function"""
    pipeline = TestPipelineFlow()
    pipeline.run_test()

if __name__ == "__main__":
    main()
