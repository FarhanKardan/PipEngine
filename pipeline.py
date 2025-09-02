import time
import pandas as pd
from datetime import datetime, timedelta
from data_feeder.data_feeder import DataFeeder
from strategies.strategy_1.ema_fractal_strategy import calculate_strategy_positions, add_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops
from logger import get_logger

class TradingPipeline:
    
    def __init__(self, symbol="XAUUSD", timeframe="M1", lookback_minutes=200):
        self.logger = get_logger("TradingPipeline")
        self.symbol = symbol
        self.timeframe = timeframe
        self.lookback_minutes = lookback_minutes
        
        self.data_feeder = DataFeeder()
        self.data_buffer = pd.DataFrame()
        self.last_update = None
        
        self.logger.info(f"Pipeline initialized for {symbol} ({timeframe})")
    
    def fetch_latest_data(self):
        """Fetch latest data and update buffer"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=self.lookback_minutes)
            
            self.logger.debug(f"Fetching data from {start_time} to {end_time}")
            
            df = self.data_feeder.get_data(
                symbol=self.symbol,
                start_date=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                interval_minutes=1,
                n_bars=self.lookback_minutes
            )
            
            if df is not None and not df.empty:
                self.data_buffer = df
                self.last_update = end_time
                self.logger.info(f"Data buffer updated: {len(df)} bars")
                return True
            else:
                self.logger.warning("No data received")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to fetch data: {e}")
            return False
    
    def process_strategy(self):
        """Process data through EMA Fractal strategy"""
        if self.data_buffer.empty:
            self.logger.warning("No data to process")
            return None
        
        try:
            self.logger.debug("Processing strategy")
            
            # Add EMA
            df, ema_col = add_ema(self.data_buffer.copy(), period=200, price_col='close')
            
            # Calculate Williams Fractal Trailing Stops
            wft_df = williams_fractal_trailing_stops(
                df, left_range=9, right_range=9, buffer_percent=0, flip_on="Close"
            )
            df = df.join(wft_df)
            
            # Calculate strategy positions
            df['strategy_position'] = calculate_strategy_positions(df, ema_col)
            
            # Get latest signal
            latest_signal = df['strategy_position'].iloc[-1]
            latest_price = df['close'].iloc[-1]
            latest_ema = df[ema_col].iloc[-1]
            
            result = {
                'timestamp': df.index[-1],
                'price': latest_price,
                'ema': latest_ema,
                'signal': latest_signal,
                'signal_text': self._get_signal_text(latest_signal)
            }
            
            self.logger.info(f"Strategy processed: {result['signal_text']} at {latest_price:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Strategy processing failed: {e}")
            return None
    
    def _get_signal_text(self, signal):
        """Convert signal number to text"""
        if signal == 1:
            return "LONG"
        elif signal == -1:
            return "SHORT"
        else:
            return "NEUTRAL"
    
    def run_iteration(self):
        """Run one iteration of the pipeline"""
        self.logger.debug("Starting pipeline iteration")
        
        # Fetch latest data
        if not self.fetch_latest_data():
            return None
        
        # Process strategy
        result = self.process_strategy()
        
        if result:
            self.logger.info(f"Iteration complete: {result['signal_text']} signal")
        
        return result
    
    def run_continuous(self, interval_seconds=60):
        """Run pipeline continuously"""
        self.logger.info(f"Starting continuous pipeline (interval: {interval_seconds}s)")
        
        try:
            while True:
                start_time = time.time()
                
                # Run iteration
                result = self.run_iteration()
                
                if result:
                    self.logger.info(f"Signal: {result['signal_text']} | Price: {result['price']:.2f} | EMA: {result['ema']:.2f}")
                
                # Wait for next iteration
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    self.logger.debug(f"Sleeping for {sleep_time:.1f} seconds")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("Pipeline stopped by user")
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")

def main():
    """Main function to run the trading pipeline"""
    logger = get_logger("Main")
    
    logger.info("Starting Trading Pipeline")
    
    # Create pipeline
    pipeline = TradingPipeline(
        symbol="XAUUSD",
        timeframe="M1", 
        lookback_minutes=200
    )
    
    # Run continuous pipeline
    pipeline.run_continuous(interval_seconds=60)

if __name__ == "__main__":
    main()
