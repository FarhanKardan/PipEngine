#!/usr/bin/env python3
"""
Simple test runner for PipEngine indicators
"""

import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def run_synthetic_tests():
    """Run only synthetic data tests"""
    from test_indicators import (
        test_ema, test_dema, test_atr, 
        test_impulse_macd, test_enhanced_zero_lag_macd, 
        test_williams_fractal_trailing_stops
    )
    
    print("🧪 Running synthetic data tests...")
    
    test_ema()
    test_dema()
    test_atr()
    test_impulse_macd()
    test_enhanced_zero_lag_macd()
    test_williams_fractal_trailing_stops()
    
    print("✅ All synthetic tests completed!")

def run_real_data_tests():
    """Run only real data tests"""
    from test_indicators import test_with_real_data, plot_test_results
    from data_feeder import DataFeeder
    
    print("🌐 Running real data tests...")
    
    results = test_with_real_data()
    if results:
        feeder = DataFeeder()
        df = feeder.fetch_data('XAUUSD', 'OANDA', n_bars=100)
        fig = plot_test_results(df, results)
        print("✅ Real data tests completed!")
        return fig
    else:
        print("⚠️ Real data tests failed")
        return None

def run_all_tests():
    """Run all tests"""
    from test_indicators import main
    main()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run PipEngine indicator tests')
    parser.add_argument('--type', choices=['synthetic', 'real', 'all'], default='all',
                       help='Type of tests to run (default: all)')
    
    args = parser.parse_args()
    
    if args.type == 'synthetic':
        run_synthetic_tests()
    elif args.type == 'real':
        run_real_data_tests()
    else:
        run_all_tests()
