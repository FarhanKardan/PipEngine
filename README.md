# PipEngine - Technical Analysis Engine

A comprehensive Python-based technical analysis engine for financial markets, featuring multiple indicators and real-time data integration.

## Features

### 📊 Technical Indicators
- **EMA** - Exponential Moving Average
- **DEMA** - Double Exponential Moving Average  
- **ATR** - Average True Range
- **Impulse MACD** - Impulse MACD system
- **Enhanced Zero Lag MACD** - Zero lag MACD with multiple options
- **Williams Fractal Trailing Stops** - Fractal-based trailing stops

### 🌐 Data Integration
- **Real-time data** from TradingView via tvDatafeed
- **Multiple exchanges** support (OANDA, etc.)
- **Flexible timeframes** (1H, 4H, 1D, etc.)
- **SSL certificate handling** for macOS compatibility

### 📈 Visualization
- **Multi-panel charts** with all indicators
- **Professional styling** and formatting
- **Export capabilities** (PNG, CSV)
- **Real-time plotting** with matplotlib

## Project Structure

```
PipEngine/
├── indicators/                 # Technical indicators
│   ├── ema.py                 # Exponential Moving Average
│   ├── dema.py                # Double Exponential Moving Average
│   ├── atr.py                 # Average True Range
│   ├── impulse_macd.py        # Impulse MACD system
│   ├── enhanced_zero_lag_macd.py  # Enhanced Zero Lag MACD
│   ├── williams_fractal_trailing_stops.py  # Williams Fractals
│   └── __init__.py            # Package exports
├── data feeder/               # Data fetching
│   └── data_feeder.py         # TradingView data integration
├── test/                      # Testing framework
│   ├── test_indicators.py     # Comprehensive test suite
│   ├── run_tests.py           # Test runner
│   └── README.md              # Testing documentation
├── main.py                    # Main application
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/FarhanKardan/PipEngine.git
cd PipEngine
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install tvDatafeed (if needed):**
```bash
pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git
```

## Usage

### 🚀 Run Main Application
```bash
python3 main.py
```

This will:
- Fetch XAUUSD data from OANDA
- Calculate all technical indicators
- Generate a comprehensive chart
- Export data to CSV
- Save chart as PNG

### 🧪 Run Tests
```bash
# All tests
cd test
python3 test_indicators.py

# Specific test types
python3 run_tests.py --type synthetic  # Synthetic data only
python3 run_tests.py --type real       # Real market data only
python3 run_tests.py --type all        # All tests (default)
```

### 📊 Use Individual Indicators
```python
from indicators.ema import calculate_ema
from indicators.dema import calculate_dema
from indicators.atr import calculate_atr

# Calculate indicators
ema_9 = calculate_ema(df['close'], 9)
dema_21 = calculate_dema(df['close'], 21)
atr_14 = calculate_atr(df, 14, 'RMA')
```

## Data Feeder

The `DataFeeder` class provides seamless access to financial data:

```python
from data_feeder import DataFeeder

# Initialize feeder
feeder = DataFeeder()

# Fetch data
df = feeder.fetch_data('XAUUSD', 'OANDA', n_bars=500)
df = feeder.fetch_xauusd()  # Convenience method
```

## Testing Framework

The comprehensive testing framework validates:
- **Synthetic data tests** - Mathematical correctness
- **Real market data tests** - Live data validation
- **Visual validation** - Chart generation and export
- **Error handling** - Robust error detection

## Requirements

- Python 3.7+
- pandas >= 1.5.0
- numpy >= 1.21.0
- matplotlib >= 3.5.0
- tvDatafeed (from GitHub)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new indicators
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Check the test results for validation
- Review the indicator implementations
- Test with synthetic data first
- Ensure data feeder connectivity
