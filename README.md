# Data Feeder

This directory contains a script to fetch historical data for XAUUSD (Gold) from the OANDA exchange using the tvDatafeed library.

## Files

- `tv_data_script.py` - Main script to fetch XAUUSD data
- `requirements.txt` - Python dependencies
- `README.md` - This documentation file

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script to fetch 500 bars of 1-hour interval data for XAUUSD:

```bash
python tv_data_script.py
```

## What it does

The script:
1. Imports the TvDatafeed library
2. Creates a TvDatafeed instance
3. Fetches 500 bars of 1-hour interval historical data for XAUUSD from OANDA exchange
4. Prints the resulting DataFrame

## Data Details

- **Symbol**: XAUUSD (Gold)
- **Exchange**: OANDA
- **Interval**: 1 hour
- **Number of bars**: 500
