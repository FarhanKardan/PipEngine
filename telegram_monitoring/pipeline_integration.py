
"""
Integration example showing how to use Telegram monitoring with the trading pipeline
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from order_tracker import OrderTracker
from config import BOT_TOKEN, CHAT_ID

class PipelineWithTelegram:
    
    def __init__(self):
        self.logger = get_logger("PipelineWithTelegram")
        self.order_tracker = OrderTracker()
        self.active_orders = {}
        self.order_counter = 0
    
    async def start(self):
        """Start the pipeline with Telegram monitoring"""
        self.logger.info("Starting pipeline with Telegram monitoring")
        await self.order_tracker.start_tracking()
    
    async def stop(self):
        """Stop the pipeline"""
        self.logger.info("Stopping pipeline")
        await self.order_tracker.stop_tracking()
    
    def create_order_from_signal(self, signal_data: dict):
        """Create an order based on trading signal"""
        if signal_data['signal'] == 0:  # Neutral signal
            return None
        
        self.order_counter += 1
        order_id = f"PIPELINE_{self.order_counter:04d}"
        
        # Determine order type based on signal
        order_type = "BUY" if signal_data['signal'] == 1 else "SELL"
        
        # Calculate SL and TP based on signal
        current_price = signal_data['price']
        if order_type == "BUY":
            sl = current_price * 0.98  # 2% stop loss
            tp = current_price * 1.02  # 2% take profit
        else:
            sl = current_price * 1.02  # 2% stop loss
            tp = current_price * 0.98  # 2% take profit
        
        order_data = {
            'order_id': order_id,
            'symbol': 'XAUUSD',
            'order_type': order_type,
            'volume': 0.1,
            'price': current_price,
            'sl': sl,
            'tp': tp,
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat()
        }
        
        # Track the order
        self.order_tracker.track_new_order(order_data)
        self.active_orders[order_id] = order_data
        
        self.logger.info(f"Order created from signal: {order_id}")
        return order_id
    
    def check_order_levels(self, current_price: float):
        """Check if any orders hit TP or SL levels"""
        orders_to_remove = []
        
        for order_id, order in self.active_orders.items():
            if order['status'] != 'ACTIVE':
                continue
            
            # Check take profit
            if order['order_type'] == 'BUY' and current_price >= order['tp']:
                profit = (current_price - order['price']) * order['volume']
                self.order_tracker.track_take_profit(order_id, order['symbol'], current_price, profit)
                orders_to_remove.append(order_id)
                self.logger.info(f"Take profit hit: {order_id}")
            
            elif order['order_type'] == 'SELL' and current_price <= order['tp']:
                profit = (order['price'] - current_price) * order['volume']
                self.order_tracker.track_take_profit(order_id, order['symbol'], current_price, profit)
                orders_to_remove.append(order_id)
                self.logger.info(f"Take profit hit: {order_id}")
            
            # Check stop loss
            elif order['order_type'] == 'BUY' and current_price <= order['sl']:
                loss = (order['price'] - current_price) * order['volume']
                self.order_tracker.track_stop_loss(order_id, order['symbol'], current_price, loss)
                orders_to_remove.append(order_id)
                self.logger.info(f"Stop loss hit: {order_id}")
            
            elif order['order_type'] == 'SELL' and current_price >= order['sl']:
                loss = (current_price - order['price']) * order['volume']
                self.order_tracker.track_stop_loss(order_id, order['symbol'], current_price, loss)
                orders_to_remove.append(order_id)
                self.logger.info(f"Stop loss hit: {order_id}")
        
        # Remove completed orders
        for order_id in orders_to_remove:
            del self.active_orders[order_id]
    
    def cancel_all_orders(self, reason: str = "Pipeline shutdown"):
        """Cancel all active orders"""
        for order_id in list(self.active_orders.keys()):
            self.order_tracker.track_order_cancelled(order_id, reason)
            del self.active_orders[order_id]
        
        self.logger.info(f"Cancelled {len(self.active_orders)} orders")

async def simulate_pipeline_with_telegram():
    """Simulate pipeline running with Telegram notifications"""
    logger = get_logger("SimulatePipeline")
    
    # Initialize pipeline
    pipeline = PipelineWithTelegram()
    await pipeline.start()
    
    try:
        # Simulate trading signals
        test_signals = [
            {'signal': 1, 'price': 2000.0, 'timestamp': datetime.now()},
            {'signal': 0, 'price': 2005.0, 'timestamp': datetime.now()},
            {'signal': -1, 'price': 2010.0, 'timestamp': datetime.now()},
            {'signal': 0, 'price': 2008.0, 'timestamp': datetime.now()},
        ]
        
        for i, signal in enumerate(test_signals):
            logger.info(f"Processing signal {i+1}: {signal}")
            
            # Create order if signal is not neutral
            order_id = pipeline.create_order_from_signal(signal)
            
            if order_id:
                logger.info(f"Created order: {order_id}")
            
            # Check existing orders for TP/SL hits
            pipeline.check_order_levels(signal['price'])
            
            # Wait between signals
            await asyncio.sleep(2)
        
        # Simulate price movements to trigger TP/SL
        logger.info("Simulating price movements...")
        
        price_movements = [2020.0, 1990.0, 2030.0, 1980.0]
        
        for price in price_movements:
            logger.info(f"Price moved to: {price}")
            pipeline.check_order_levels(price)
            await asyncio.sleep(1)
        
        logger.info("Simulation completed")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
    
    finally:
        # Cancel any remaining orders
        pipeline.cancel_all_orders("Simulation ended")
        await pipeline.stop()

def main():
    """Main function"""
    print("🤖 Pipeline with Telegram Integration")
    print("=" * 50)
    print("This example shows how to integrate Telegram monitoring")
    print("with your trading pipeline for real-time notifications.")
    print("=" * 50)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please configure BOT_TOKEN and CHAT_ID in config.py")
        return
    
    # Run the simulation
    asyncio.run(simulate_pipeline_with_telegram())

if __name__ == "__main__":
    main()
