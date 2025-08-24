# MetaTrader Client Package

A Python client for communicating with MetaTrader through the REST API. This package provides a comprehensive interface for retrieving market data, managing trading operations, and accessing account information.

## Features

- **Price History Retrieval**: Get OHLCV data for any symbol and timeframe
- **Account Management**: Access account information, balance, and equity
- **Trading Operations**: Place orders, manage positions, and monitor trades
- **Symbol Information**: Get available trading symbols and their details
- **Server Time**: Synchronize with MetaTrader server time
- **Error Handling**: Comprehensive error handling and connection testing

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Import the client:
```python
from meta_client import MetaTraderClient
```

## Quick Start

```python
from meta_client import MetaTraderClient

# Initialize client
client = MetaTraderClient(
    base_url="http://trade-api.reza-developer.com",
    api_key="your_api_key_here"  # Optional
)

# Test connection
if client.test_connection():
    print("Connected to MetaTrader!")
    
    # Get price history
    df = client.get_price_history("XAUUSD", "M1", count=100)
    print(f"Retrieved {len(df)} bars")
```

## API Reference

### Core Methods

#### `get_price_history(symbol, timeframe, start_time, end_time, count)`
Retrieve price history data for a symbol.

**Parameters:**
- `symbol` (str): Trading symbol (e.g., "XAUUSD", "EURUSD")
- `timeframe` (str): Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
- `start_time` (datetime/str, optional): Start time for data
- `end_time` (datetime/str, optional): End time for data
- `count` (int, optional): Number of bars to retrieve

**Returns:** pandas DataFrame with OHLCV data

#### `get_account_info()`
Get account information including balance, equity, and login details.

**Returns:** Dictionary with account information

#### `get_symbols()`
Get list of available trading symbols.

**Returns:** List of symbol dictionaries

#### `place_order(symbol, order_type, volume, price, stop_loss, take_profit, comment)`
Place a trading order.

**Parameters:**
- `symbol` (str): Trading symbol
- `order_type` (str): Order type (BUY, SELL, BUY_LIMIT, SELL_LIMIT)
- `volume` (float): Order volume
- `price` (float, optional): Order price for limit orders
- `stop_loss` (float, optional): Stop loss price
- `take_profit` (float, optional): Take profit price
- `comment` (str, optional): Order comment

**Returns:** Order response from API

#### `get_positions(symbol)`
Get open positions, optionally filtered by symbol.

**Parameters:**
- `symbol` (str, optional): Filter by specific symbol

**Returns:** List of open positions

#### `get_orders(symbol)`
Get open orders, optionally filtered by symbol.

**Parameters:**
- `symbol` (str, optional): Filter by specific symbol

**Returns:** List of open orders

### Utility Methods

#### `test_connection()`
Test the connection to the MetaTrader API.

**Returns:** Boolean indicating connection status

#### `get_server_time()`
Get the current server time from MetaTrader.

**Returns:** datetime object with server time

## Examples

### Get Recent Price Data
```python
# Get last 100 M1 bars for XAUUSD
df = client.get_price_history("XAUUSD", "M1", count=100)

# Get data for specific time range
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(days=7)
df = client.get_price_history("XAUUSD", "H1", start_time, end_time)
```

### Place a Market Order
```python
# Place a market buy order
order = client.place_order(
    symbol="XAUUSD",
    order_type="BUY",
    volume=0.1,
    stop_loss=2000.0,
    take_profit=2100.0,
    comment="Strategy entry"
)
```

### Monitor Positions
```python
# Get all open positions
positions = client.get_positions()

# Get positions for specific symbol
xauusd_positions = client.get_positions("XAUUSD")

for pos in positions:
    print(f"{pos['symbol']}: {pos['type']} {pos['volume']} @ {pos['price']}")
```

## Error Handling

The client includes comprehensive error handling:

```python
try:
    df = client.get_price_history("XAUUSD", "M1", count=100)
    if not df.empty:
        print(f"Retrieved {len(df)} bars")
    else:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")
```

## Configuration

### Base URL
The default base URL is `http://trade-api.reza-developer.com`. You can customize this:

```python
client = MetaTraderClient(
    base_url="https://your-custom-endpoint.com",
    api_key="your_key"
)
```

### API Key
If your MetaTrader API requires authentication, provide an API key:

```python
client = MetaTraderClient(api_key="your_api_key_here")
```

## Dependencies

- `requests`: HTTP library for API communication
- `pandas`: Data manipulation and analysis
- `python-dateutil`: Date parsing utilities

## License

This package is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the API documentation at [http://trade-api.reza-developer.com/docs/v1](http://trade-api.reza-developer.com/docs/v1)
2. Review the example usage script
3. Ensure your MetaTrader setup supports REST API access

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this package.
