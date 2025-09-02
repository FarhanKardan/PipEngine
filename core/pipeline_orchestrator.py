import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from data_feeder.data_feeder import DataFeeder
from core.signal_generator import SignalGenerator
from core.position_tracker import PositionTracker
from core.notification_manager import NotificationManager
from logger import get_logger

class PipelineOrchestrator:
    """Orchestrates the trading pipeline with optimized data flow"""
    
    def __init__(self, symbol: str = "XAUUSD", 
                 ema_period: int = 200,
                 take_profit_pips: int = 50,
                 stop_loss_pips: int = 30):
        self.logger = get_logger("PipelineOrchestrator")
        self.symbol = symbol
        
        # Initialize components
        self.data_feeder = DataFeeder()
        self.signal_generator = SignalGenerator(ema_period=ema_period)
        self.position_tracker = PositionTracker(
            take_profit_pips=take_profit_pips,
            stop_loss_pips=stop_loss_pips
        )
        self.notification_manager = NotificationManager()
        
        # Cache for optimization
        self._last_data = None
        self._last_timestamp = None
        
        self.logger.info(f"Pipeline initialized for {symbol}")
    
    async def get_latest_data(self, n_bars: int = 200) -> Optional[object]:
        """Get latest data with caching optimization"""
        try:
            # Use cached data if it's recent (within 30 seconds)
            now = datetime.now()
            if (self._last_data is not None and 
                self._last_timestamp is not None and 
                (now - self._last_timestamp).seconds < 30):
                return self._last_data
            
            end_time = now
            start_time = end_time - timedelta(minutes=n_bars)
            
            df = self.data_feeder.get_data(
                symbol=self.symbol,
                start_date=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                interval_minutes=1,
                n_bars=n_bars
            )
            
            if df is not None and not df.empty:
                self._last_data = df
                self._last_timestamp = now
                self.logger.info(f"Fetched {len(df)} bars")
                return df
            else:
                self.logger.warning("No data received")
                return None
                
        except Exception as e:
            self.logger.error(f"Data fetch failed: {e}")
            return None
    
    async def process_signal(self, df) -> Optional[Dict[str, Any]]:
        """Process data and generate signal"""
        try:
            # Process data through signal generator
            processed_df = self.signal_generator.process_data(df)
            if processed_df is None:
                return None
            
            # Get latest signal
            signal = self.signal_generator.get_latest_signal(processed_df)
            return signal
            
        except Exception as e:
            self.logger.error(f"Signal processing failed: {e}")
            return None
    
    async def handle_position_logic(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle position opening/closing logic"""
        try:
            signal_value = signal['signal']
            price = signal['price']
            timestamp = signal['timestamp']
            
            # Check for position changes
            if signal_value != 0 and not self.position_tracker.has_position:
                # Open new position
                event_data = self.position_tracker.open_position(signal_value, price, timestamp)
                if event_data:
                    await self.notification_manager.handle_position_event(self.symbol, event_data)
                    return event_data
                    
            elif signal_value == 0 and self.position_tracker.has_position:
                # Close position
                event_data = self.position_tracker.close_position(price, timestamp)
                if event_data:
                    await self.notification_manager.handle_position_event(self.symbol, event_data)
                    return event_data
            
            # Check for TP/SL if position is open
            if self.position_tracker.has_position:
                tp_sl_event = self.position_tracker.check_tp_sl(price, timestamp)
                if tp_sl_event:
                    await self.notification_manager.handle_position_event(self.symbol, tp_sl_event)
                    return tp_sl_event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Position logic failed: {e}")
            return None
    
    async def run_single_iteration(self) -> Optional[Dict[str, Any]]:
        """Run one complete iteration"""
        try:
            # Get data
            df = await self.get_latest_data()
            if df is None:
                return None
            
            # Process signal
            signal = await self.process_signal(df)
            if signal is None:
                return None
            
            self.logger.info(f"Signal: {signal['signal_text']} | Price: {signal['price']:.2f}")
            
            # Handle position logic
            position_event = await self.handle_position_logic(signal)
            
            return {
                'signal': signal,
                'position_event': position_event
            }
            
        except Exception as e:
            self.logger.error(f"Iteration failed: {e}")
            return None
    
    async def run_until_signal(self, delay_seconds: int = 1) -> Dict[str, Any]:
        """Run continuously until a trading signal is generated"""
        self.logger.info(f"Starting continuous monitoring (delay: {delay_seconds}s)")
        
        # Send startup notification
        await self.notification_manager.send_startup_notification(self.symbol)
        
        iteration = 0
        try:
            while True:
                iteration += 1
                self.logger.info(f"--- Iteration {iteration} ---")
                
                result = await self.run_single_iteration()
                
                if result and result['signal']:
                    signal = result['signal']
                    print(f"[{signal['timestamp']}] {signal['signal_text']} | Price: {signal['price']:.2f} | EMA: {signal['ema']:.2f}")
                    
                    # Check if we got a trading signal (LONG or SHORT)
                    if signal['signal'] != 0:
                        self.logger.info(f"🎯 Trading signal generated: {signal['signal_text']} at {signal['price']:.2f}")
                        print(f"\n🎉 SIGNAL GENERATED: {signal['signal_text']} at {signal['price']:.2f}")
                        break
                
                # Wait before next iteration
                await asyncio.sleep(delay_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("Pipeline stopped by user")
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")
        finally:
            # Send shutdown notification
            await self.notification_manager.send_shutdown_notification()
        
        self.logger.info("Signal generation completed")
        return result or {}
