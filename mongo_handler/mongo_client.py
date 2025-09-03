import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from logger import get_logger
from config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME, MONGODB_TRADING_COLLECTION

class MongoHandler:
    
    def __init__(self, connection_string: str = None, 
                 database_name: str = None, collection_name: str = None):
        self.logger = get_logger("MongoHandler")
        self.connection_string = connection_string or MONGODB_CONNECTION_STRING
        self.database_name = database_name or MONGODB_DATABASE_NAME
        self.collection_name = collection_name or MONGODB_TRADING_COLLECTION
        self.client = None
        self.database = None
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            self.logger.info(f"Connected to MongoDB: {self.database_name}.{self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.database = None
            self.collection = None
    
    def check_connection(self) -> bool:
        """Check if connected to MongoDB"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
    
    def add_record(self, document: Dict) -> Optional[str]:
        """Add a single record"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return None
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in document:
                document['timestamp'] = datetime.now()
            
            result = self.collection.insert_one(document)
            self.logger.info(f"Record added with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Failed to add record: {e}")
            return None
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return None
        
        try:
            document = self.collection.find_one({'order_id': order_id})
            if document:
                self.logger.info(f"Found order: {order_id}")
            else:
                self.logger.info(f"Order not found: {order_id}")
            return document
            
        except Exception as e:
            self.logger.error(f"Failed to get order: {e}")
            return None
    
    def add_order(self, order_data: Dict) -> Optional[str]:
        """Add a new order to the database"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return None
        
        try:
            # Ensure required fields
            required_fields = ['order_id', 'symbol', 'order_type', 'volume', 'price']
            for field in required_fields:
                if field not in order_data:
                    self.logger.error(f"Missing required field: {field}")
                    return None
            
            # Add timestamp if not present
            if 'timestamp' not in order_data:
                order_data['timestamp'] = datetime.now()
            
            # Set default status if not provided
            if 'status' not in order_data:
                order_data['status'] = 'ACTIVE'
            
            # Check if order already exists
            existing = self.collection.find_one({'order_id': order_data['order_id']})
            if existing:
                self.logger.warning(f"Order {order_data['order_id']} already exists")
                return None
            
            result = self.collection.insert_one(order_data)
            self.logger.info(f"Order added: {order_data['order_id']} - {order_data['symbol']} {order_data['order_type']}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Failed to add order: {e}")
            return None
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return []
        
        try:
            query = {'status': 'ACTIVE'}
            orders = list(self.collection.find(query).sort('timestamp', -1))
            
            self.logger.info(f"Found {len(orders)} active orders")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get active orders: {e}")
            return []
    
    def get_orders_by_symbol(self, symbol: str) -> List[Dict]:
        """Get all orders for a specific symbol"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return []
        
        try:
            query = {'symbol': symbol.upper()}
            orders = list(self.collection.find(query).sort('timestamp', -1))
            
            self.logger.info(f"Found {len(orders)} orders for {symbol}")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders for {symbol}: {e}")
            return []
    
    def get_orders_by_status(self, status: str) -> List[Dict]:
        """Get all orders with a specific status"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return []
        
        try:
            query = {'status': status.upper()}
            orders = list(self.collection.find(query).sort('timestamp', -1))
            
            self.logger.info(f"Found {len(orders)} orders with status {status}")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders with status {status}: {e}")
            return []
    
    def update_order_status(self, order_id: str, new_status: str, additional_data: Dict = None) -> bool:
        """Update order status and optionally add additional data"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return False
        
        try:
            update_data = {
                'status': new_status.upper(),
                'updated_at': datetime.now()
            }
            
            # Add additional data if provided
            if additional_data:
                update_data.update(additional_data)
            
            result = self.collection.update_one(
                {'order_id': order_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Order {order_id} status updated to {new_status}")
                return True
            else:
                self.logger.warning(f"Order {order_id} not found or not modified")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update order {order_id}: {e}")
            return False
    
    def close_order(self, order_id: str, exit_price: float, profit: float = None) -> bool:
        """Close an order with exit price and profit"""
        additional_data = {
            'exit_price': exit_price,
            'closed_at': datetime.now()
        }
        
        if profit is not None:
            additional_data['profit'] = profit
        
        return self.update_order_status(order_id, 'CLOSED', additional_data)
    
    def cancel_order(self, order_id: str, reason: str = None) -> bool:
        """Cancel an order with optional reason"""
        additional_data = {
            'cancelled_at': datetime.now()
        }
        
        if reason:
            additional_data['cancel_reason'] = reason
        
        return self.update_order_status(order_id, 'CANCELLED', additional_data)
    
    def get_last_24h_orders_report(self) -> Optional[Dict]:
        """Get orders from last 24 hours and return a basic report"""
        if not self.check_connection():
            self.logger.error("Not connected to MongoDB")
            return None
        
        try:
            # Calculate 24 hours ago
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            
            # Query orders from last 24 hours
            query = {
                'timestamp': {
                    '$gte': twenty_four_hours_ago
                }
            }
            
            orders = list(self.collection.find(query))
            total_orders = len(orders)
            
            if total_orders == 0:
                return {
                    'period': 'Last 24 hours',
                    'total_orders': 0,
                    'message': 'No orders found in the last 24 hours'
                }
            
            # Calculate statistics
            buy_orders = sum(1 for order in orders if order.get('order_type') == 'BUY')
            sell_orders = sum(1 for order in orders if order.get('order_type') == 'SELL')
            
            active_orders = sum(1 for order in orders if order.get('status') == 'ACTIVE')
            closed_orders = sum(1 for order in orders if order.get('status') in ['CLOSED', 'CLOSED_TP', 'CLOSED_SL'])
            cancelled_orders = sum(1 for order in orders if order.get('status') == 'CANCELLED')
            
            # Get unique symbols
            symbols = list(set(order.get('symbol', 'Unknown') for order in orders))
            
            # Calculate total volume
            total_volume = sum(order.get('volume', 0) for order in orders)
            
            # Calculate average price
            prices = [order.get('price', 0) for order in orders if order.get('price')]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            # Get profit/loss if available
            profits = [order.get('profit', 0) for order in orders if order.get('profit') is not None]
            total_profit = sum(profits)
            
            report = {
                'period': 'Last 24 hours',
                'total_orders': total_orders,
                'order_types': {
                    'buy_orders': buy_orders,
                    'sell_orders': sell_orders
                },
                'order_status': {
                    'active': active_orders,
                    'closed': closed_orders,
                    'cancelled': cancelled_orders
                },
                'symbols_traded': symbols,
                'total_volume': round(total_volume, 2),
                'average_price': round(avg_price, 2),
                'total_profit': round(total_profit, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated 24h report: {total_orders} orders found")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate 24h report: {e}")
            return None
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
    
    def __del__(self):
        """Destructor to close connection"""
        self.close_connection()

# Example usage
def main():
    """Example usage of MongoDB handler"""
    print("🍃 MongoDB Handler Example")
    print("=" * 40)
    
    # Initialize handler
    handler = MongoHandler()
    
    if not handler.check_connection():
        print("❌ Failed to connect to MongoDB")
        print("Make sure MongoDB is running on localhost:27017")
        return
    
    print("✅ Connected to MongoDB")
    
    # Example: Add orders using the new add_order method
    orders_to_add = [
        {
            'order_id': 'ORDER_001',
            'symbol': 'XAUUSD',
            'order_type': 'BUY',
            'volume': 0.1,
            'price': 2000.0,
            'sl': 1950.0,
            'tp': 2050.0
        },
        {
            'order_id': 'ORDER_002',
            'symbol': 'EURUSD',
            'order_type': 'SELL',
            'volume': 0.2,
            'price': 1.0850,
            'sl': 1.0900,
            'tp': 1.0800
        },
        {
            'order_id': 'ORDER_003',
            'symbol': 'XAUUSD',
            'order_type': 'BUY',
            'volume': 0.15,
            'price': 2010.0,
            'sl': 1960.0,
            'tp': 2060.0
        }
    ]
    
    print("📝 Adding orders...")
    for order_data in orders_to_add:
        doc_id = handler.add_order(order_data)
        if doc_id:
            print(f"✅ Order added: {order_data['order_id']} - {order_data['symbol']} {order_data['order_type']}")
    
    # Example: Get active orders
    print("\n📊 Active Orders:")
    print("-" * 30)
    active_orders = handler.get_active_orders()
    for order in active_orders:
        print(f"🟢 {order['order_id']} - {order['symbol']} {order['order_type']} @ {order['price']}")
    
    # Example: Get orders by symbol
    print(f"\n📊 XAUUSD Orders:")
    print("-" * 30)
    xauusd_orders = handler.get_orders_by_symbol('XAUUSD')
    for order in xauusd_orders:
        print(f"📈 {order['order_id']} - {order['order_type']} @ {order['price']} - {order['status']}")
    
    # Example: Update order status
    print(f"\n🔄 Updating order status...")
    success = handler.update_order_status('ORDER_001', 'CLOSED', {'exit_price': 2025.0, 'profit': 25.0})
    if success:
        print("✅ Order ORDER_001 closed successfully")
    
    # Example: Close order
    success = handler.close_order('ORDER_002', 1.0820, -6.0)
    if success:
        print("✅ Order ORDER_002 closed with loss")
    
    # Example: Cancel order
    success = handler.cancel_order('ORDER_003', 'Manual cancellation')
    if success:
        print("✅ Order ORDER_003 cancelled")
    
    # Example: Get orders by status
    print(f"\n📊 Closed Orders:")
    print("-" * 30)
    closed_orders = handler.get_orders_by_status('CLOSED')
    for order in closed_orders:
        profit = order.get('profit', 0)
        print(f"🔴 {order['order_id']} - {order['symbol']} - Profit: {profit}")
    
    # Example: Get 24h report
    print("\n📈 24-Hour Trading Report:")
    print("-" * 40)
    report = handler.get_last_24h_orders_report()
    if report:
        if report['total_orders'] == 0:
            print(f"📊 {report['message']}")
        else:
            print(f"📊 Period: {report['period']}")
            print(f"📊 Total Orders: {report['total_orders']}")
            print(f"📊 Buy Orders: {report['order_types']['buy_orders']}")
            print(f"📊 Sell Orders: {report['order_types']['sell_orders']}")
            print(f"📊 Active: {report['order_status']['active']}")
            print(f"📊 Closed: {report['order_status']['closed']}")
            print(f"📊 Cancelled: {report['order_status']['cancelled']}")
            print(f"📊 Symbols: {', '.join(report['symbols_traded'])}")
            print(f"📊 Total Volume: {report['total_volume']}")
            print(f"📊 Average Price: {report['average_price']}")
            print(f"📊 Total Profit: {report['total_profit']}")
    else:
        print("❌ Failed to generate report")
    
    # Close connection
    handler.close_connection()
    print("\n🔌 Connection closed")

if __name__ == "__main__":
    main()
