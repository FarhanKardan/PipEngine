#!/usr/bin/env python3
"""
Main application - fetches XAUUSD data, calculates EMA and DEMA, exports to CSV
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'indicators'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'data feeder'))

# Import modules
from indicators.ema import calculate_multiple_ema
from indicators.dema import calculate_dema
from data_feeder import DataFeeder

def main():
    try:
        # Initialize and fetch data
        feeder = DataFeeder('mohammadtrade1404@gmail.com', 'YourTradingViewPassword')
        df = feeder.fetch_xauusd()
        
        if df is None or df.empty:
            print("❌ No data received")
            return
        
        # Calculate indicators
        ema_data = calculate_multiple_ema(df['close'], [9, 21, 50])
        dema_9 = calculate_dema(df['close'], 9)
        dema_21 = calculate_dema(df['close'], 21)
        
        # Combine data
        result_df = df.copy()
        for col in ema_data.columns:
            result_df[col] = ema_data[col]
        result_df['DEMA_9'] = dema_9
        result_df['DEMA_21'] = dema_21
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"XAUUSD_Analysis_{timestamp}.csv"
        result_df.to_csv(filename, index=True)
        
        print(f"✅ Data saved: {len(result_df)} rows to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
