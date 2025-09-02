import pymongo
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, Optional
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
    
    # Example: Add order record
    order_data = {
        'order_id': 'ORDER_001',
        'symbol': 'XAUUSD',
        'order_type': 'BUY',
        'volume': 0.1,
        'price': 2000.0,
        'sl': 1950.0,
        'tp': 2050.0,
        'status': 'ACTIVE'
    }
    
    doc_id = handler.add_record(order_data)
    if doc_id:
        print(f"✅ Order added with ID: {doc_id}")
    
    # Example: Get order by ID
    order = handler.get_order_by_id('ORDER_001')
    if order:
        print(f"📊 Retrieved order: {order['order_id']} - {order['symbol']}")
    
    # Close connection
    handler.close_connection()
    print("🔌 Connection closed")

if __name__ == "__main__":
    main()
