import time
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from data_feeder.data_feeder import DataFeeder
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops
from logger import get_logger

def add_ema(df, period=200, price_col='close'):
    """Add EMA to dataframe"""
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def calculate_strategy_positions(df, ema_col='ema_200'):
    """Calculate strategy positions based on EMA and Williams Fractal logic"""
    long_positions = []
    short_positions = []
    
    # Long position tracking
    long_position_open = False
    long_target_price = None
    long_pending_entry = False
    
    # Short position tracking
    short_position_open = False
    short_target_price = None
    short_pending_entry = False

    for i in range(len(df)):
        open_i  = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        ema_i   = df[ema_col].iloc[i]
        ema200_i = df[ema_col].iloc[i]

        current_long_pos = 0
        current_short_pos = 0

        # === LONG POSITION LOGIC ===
        # Invalidate target price if a low fractal appears
        if 'williams_low_price' in df.columns and not pd.isna(df['williams_low_price'].iloc[i]):
            long_target_price = None
            long_pending_entry = False

        # Update reference price if high fractal appears AND price above EMA
        if not pd.isna(df['williams_high_price'].iloc[i]) and close_i > ema_i:
            long_target_price = float(df['high'].iloc[i])
            long_pending_entry = False

        # Enter long on this candle if a pending entry was flagged
        if not long_position_open and long_pending_entry:
            long_position_open = True
            long_pending_entry = False
            current_long_pos = 1

        # Entry logic: check if at least 50% of body is above reference AND price above EMA200
        elif not long_position_open and long_target_price is not None and close_i > ema_i and close_i > ema200_i:
            body = abs(close_i - open_i)
            if body > 0:
                top = max(open_i, close_i)
                bot = min(open_i, close_i)

                if top <= long_target_price:
                    body_above = 0
                elif bot >= long_target_price:
                    body_above = body
                else:
                    body_above = top - long_target_price

                if body_above >= 0.5 * body:
                    long_pending_entry = True

        # Exit long logic
        elif long_position_open and close_i < ema_i:
            long_position_open = False
            current_long_pos = 0
        elif long_position_open:
            current_long_pos = 1

        # === SHORT POSITION LOGIC ===
        # Invalidate target price if ANY fractal appears between
        if (
            ('williams_high_price' in df.columns and not pd.isna(df['williams_high_price'].iloc[i])) or
            ('williams_low_price' in df.columns and not pd.isna(df['williams_low_price'].iloc[i]) and short_target_price is not None)
        ):
            short_target_price = None
            short_pending_entry = False

        # Update reference price only if low fractal appears AND price below EMA
        if not pd.isna(df['williams_low_price'].iloc[i]) and close_i < ema_i:
            short_target_price = float(df['low'].iloc[i])
            short_pending_entry = False

        # Enter short on this candle if a pending entry was flagged
        if not short_position_open and short_pending_entry:
            short_position_open = True
            short_pending_entry = False
            current_short_pos = -1

        # Entry logic: 50% body below target & below EMA200
        elif not short_position_open and short_target_price is not None and close_i < ema_i and close_i < ema200_i:
            body = abs(close_i - open_i)
            if body > 0:
                top = max(open_i, close_i)
                bot = min(open_i, close_i)

                if bot >= short_target_price:
                    body_below = 0
                elif top <= short_target_price:
                    body_below = body
                else:
                    body_below = short_target_price - bot

                if body_below >= 0.5 * body:
                    short_pending_entry = True

        # Exit short when price crosses above EMA
        elif short_position_open and close_i > ema_i:
            short_position_open = False
            current_short_pos = 0
        elif short_position_open:
            current_short_pos = -1

        long_positions.append(current_long_pos)
        short_positions.append(current_short_pos)

    # Combine long and short positions (long takes precedence if both exist)
    combined_positions = []
    for long_pos, short_pos in zip(long_positions, short_positions):
        if long_pos == 1:
            combined_positions.append(1)  # Long position
        elif short_pos == -1:
            combined_positions.append(-1)  # Short position
        else:
            combined_positions.append(0)   # Neutral

    return pd.Series(combined_positions, index=df.index).astype(int)

class SimplePipeline:
    
    def __init__(self, symbol="XAUUSD"):
        self.logger = get_logger("SimplePipeline")
        self.symbol = symbol
        self.data_feeder = DataFeeder()
        self.logger.info(f"Simple pipeline initialized for {symbol}")
    
    def get_latest_data(self):
        """Get latest 200 bars of data"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=200)
            
            df = self.data_feeder.get_data(
                symbol=self.symbol,
                start_date=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                interval_minutes=1,
                n_bars=200
            )
            
            if df is not None and not df.empty:
                self.logger.info(f"Fetched {len(df)} bars")
                return df
            else:
                self.logger.warning("No data received")
                return None
                
        except Exception as e:
            self.logger.error(f"Data fetch failed: {e}")
            return None
    
    def process_data(self, df):
        """Process data through strategy"""
        try:
            # Add EMA
            df, ema_col = add_ema(df.copy(), period=200, price_col='close')
            
            # Add Williams Fractal
            wft_df = williams_fractal_trailing_stops(
                df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close"
            )
            df = df.join(wft_df)
            
            # Calculate signals
            df['strategy_position'] = calculate_strategy_positions(df, ema_col)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return None
    
    def get_latest_signal(self, df):
        """Get the latest trading signal"""
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        signal = latest['strategy_position']
        
        signal_text = "LONG" if signal == 1 else "SHORT" if signal == -1 else "NEUTRAL"
        
        return {
            'timestamp': df.index[-1],
            'price': latest['close'],
            'ema': latest['ema_200'],
            'signal': signal,
            'signal_text': signal_text
        }
    
    def run_single_iteration(self):
        """Run one complete iteration"""
        self.logger.info("Running single iteration")
        
        # Get data
        df = self.get_latest_data()
        if df is None:
            return None
        
        # Process data
        processed_df = self.process_data(df)
        if processed_df is None:
            return None
        
        # Get signal
        signal = self.get_latest_signal(processed_df)
        
        if signal:
            self.logger.info(f"Signal: {signal['signal_text']} | Price: {signal['price']:.2f}")
        
        return signal
    
    def run_loop(self, iterations=10, delay_seconds=60):
        """Run multiple iterations with delay"""
        self.logger.info(f"Starting loop: {iterations} iterations, {delay_seconds}s delay")
        
        for i in range(iterations):
            self.logger.info(f"--- Iteration {i+1}/{iterations} ---")
            
            signal = self.run_single_iteration()
            
            if signal:
                print(f"[{signal['timestamp']}] {signal['signal_text']} | Price: {signal['price']:.2f} | EMA: {signal['ema']:.2f}")
            
            if i < iterations - 1:  # Don't sleep after last iteration
                self.logger.info(f"Waiting {delay_seconds} seconds...")
                time.sleep(delay_seconds)
        
        self.logger.info("Loop completed")

def main():
    """Test the simple pipeline"""
    logger = get_logger("Main")
    
    logger.info("Starting Simple Pipeline Test")
    
    pipeline = SimplePipeline("XAUUSD")
    
    # Run 5 iterations with 10 second delay for testing
    pipeline.run_loop(iterations=5, delay_seconds=10)

if __name__ == "__main__":
    main()
