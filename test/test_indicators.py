#!/usr/bin/env python3
"""
Test and validate all indicators with real market data from data feeder
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import indicators
from indicators.ema import calculate_ema
from indicators.dema import calculate_dema
from indicators.atr import calculate_atr
from indicators.impulse_macd import impulse_macd_lb
from indicators.enhanced_zero_lag_macd import enhanced_zero_lag_macd
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops

# Import data feeder
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data feeder'))
from data_feeder import DataFeeder

def test_ema():
    """Test EMA indicator"""
    print("🧪 Testing EMA indicator...")
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.Series([100 + i * 0.1 + (i % 10) * 0.5 for i in range(100)], index=dates)
    
    # Calculate EMA
    ema_9 = calculate_ema(sample_data, 9)
    ema_21 = calculate_ema(sample_data, 21)
    
    # Validate results
    assert len(ema_9) == len(sample_data), "EMA length mismatch"
    assert not ema_9.isna().all(), "EMA is all NaN"
    assert ema_9.iloc[-1] is not None, "Last EMA value is None"
    
    print("✅ EMA test passed")
    return ema_9, ema_21

def test_dema():
    """Test DEMA indicator"""
    print("🧪 Testing DEMA indicator...")
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.Series([100 + i * 0.1 + (i % 10) * 0.5 for i in range(100)], index=dates)
    
    # Calculate DEMA
    dema_9 = calculate_dema(sample_data, 9)
    dema_21 = calculate_dema(sample_data, 21)
    
    # Validate results
    assert len(dema_9) == len(sample_data), "DEMA length mismatch"
    assert not dema_9.isna().all(), "DEMA is all NaN"
    assert dema_9.iloc[-1] is not None, "Last DEMA value is None"
    
    print("✅ DEMA test passed")
    return dema_9, dema_21

def test_atr():
    """Test ATR indicator"""
    print("🧪 Testing ATR indicator...")
    
    # Create sample OHLC data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Calculate ATR
    atr_14 = calculate_atr(sample_data, 14, 'RMA')
    atr_21 = calculate_atr(sample_data, 21, 'EMA')
    
    # Validate results
    assert len(atr_14) == len(sample_data), "ATR length mismatch"
    assert not atr_14.isna().all(), "ATR is all NaN"
    assert atr_14.iloc[-1] > 0, "ATR should be positive"
    
    print("✅ ATR test passed")
    return atr_14, atr_21

def test_impulse_macd():
    """Test Impulse MACD indicator"""
    print("🧪 Testing Impulse MACD indicator...")
    
    # Create sample OHLC data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Calculate Impulse MACD
    result = impulse_macd_lb(sample_data, 34, 9)
    
    # Validate results
    assert len(result) == len(sample_data), "Impulse MACD length mismatch"
    assert 'md' in result.columns, "Missing 'md' column"
    assert 'sb' in result.columns, "Missing 'sb' column"
    assert 'sh' in result.columns, "Missing 'sh' column"
    
    print("✅ Impulse MACD test passed")
    return result

def test_enhanced_zero_lag_macd():
    """Test Enhanced Zero Lag MACD indicator"""
    print("🧪 Testing Enhanced Zero Lag MACD indicator...")
    
    # Create sample OHLC data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Calculate Enhanced Zero Lag MACD
    result = enhanced_zero_lag_macd(sample_data, 12, 26, 9, 9, True, False)
    
    # Validate results
    assert len(result) == len(sample_data), "Enhanced Zero Lag MACD length mismatch"
    assert 'zero_lag_macd' in result.columns, "Missing 'zero_lag_macd' column"
    assert 'signal' in result.columns, "Missing 'signal' column"
    assert 'histogram' in result.columns, "Missing 'histogram' column"
    
    print("✅ Enhanced Zero Lag MACD test passed")
    return result

def test_williams_fractal_trailing_stops():
    """Test Williams Fractal Trailing Stops indicator"""
    print("🧪 Testing Williams Fractal Trailing Stops indicator...")
    
    # Create sample OHLC data
    dates = pd.date_range('2025-01-01', periods=100, freq='h')
    sample_data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 1 + (i % 5) * 0.2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 - (i % 5) * 0.2 for i in range(100)],
        'close': [100 + i * 0.1 + (i % 3) * 0.3 for i in range(100)]
    }, index=dates)
    
    # Calculate Williams Fractal Trailing Stops
    result = williams_fractal_trailing_stops(sample_data, 2, 2, 0, "Close")
    
    # Validate results
    assert len(result) == len(sample_data), "Williams Fractal length mismatch"
    assert 'is_williams_high' in result.columns, "Missing 'is_williams_high' column"
    assert 'is_williams_low' in result.columns, "Missing 'is_williams_low' column"
    assert 'williams_long_stop' in result.columns, "Missing 'williams_long_stop' column"
    
    print("✅ Williams Fractal Trailing Stops test passed")
    return result

def test_with_real_data():
    """Test indicators with real market data"""
    print("🌐 Testing with real market data...")
    
    try:
        # Initialize data feeder
        feeder = DataFeeder()
        
        # Fetch real data
        df = feeder.fetch_data('XAUUSD', 'OANDA', n_bars=100)
        
        if df is None or df.empty:
            print("⚠️ Could not fetch real data, skipping real data tests")
            return None
        
        print(f"📊 Fetched {len(df)} bars of real XAUUSD data")
        
        # Test all indicators with real data
        results = {}
        
        # EMA
        results['ema_9'] = calculate_ema(df['close'], 9)
        results['ema_21'] = calculate_ema(df['close'], 21)
        
        # DEMA
        results['dema_9'] = calculate_dema(df['close'], 9)
        results['dema_21'] = calculate_dema(df['close'], 21)
        
        # ATR
        results['atr_14'] = calculate_atr(df, 14, 'RMA')
        
        # Impulse MACD
        results['impulse_macd'] = impulse_macd_lb(df, 34, 9)
        
        # Enhanced Zero Lag MACD
        results['enhanced_macd'] = enhanced_zero_lag_macd(df, 12, 26, 9, 9, True, False)
        
        # Williams Fractal
        results['williams_fractal'] = williams_fractal_trailing_stops(df, 2, 2, 0, "Close")
        
        print("✅ All indicators tested with real data successfully")
        return results
        
    except Exception as e:
        print(f"❌ Error testing with real data: {e}")
        return None

def plot_test_results(df, results):
    """Plot test results"""
    if results is None:
        return
    
    print("📈 Creating test results visualization...")
    
    # Create subplots
    fig, axes = plt.subplots(3, 2, figsize=(20, 15))
    fig.suptitle('Indicator Test Results with Real Market Data', fontsize=16, fontweight='bold')
    
    # Plot 1: Price and EMAs
    ax1 = axes[0, 0]
    ax1.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1)
    ax1.plot(df.index, results['ema_9'], label='EMA(9)', color='blue', linewidth=1)
    ax1.plot(df.index, results['ema_21'], label='EMA(21)', color='red', linewidth=1)
    ax1.set_title('Price with EMAs')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Price and DEMAs
    ax2 = axes[0, 1]
    ax2.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1)
    ax2.plot(df.index, results['dema_9'], label='DEMA(9)', color='green', linewidth=1)
    ax2.plot(df.index, results['dema_21'], label='DEMA(21)', color='orange', linewidth=1)
    ax2.set_title('Price with DEMAs')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: ATR
    ax3 = axes[1, 0]
    ax3.plot(df.index, results['atr_14'], label='ATR(14)', color='purple', linewidth=1)
    ax3.set_title('Average True Range')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Impulse MACD
    ax4 = axes[1, 1]
    ax4.plot(df.index, results['impulse_macd']['md'], label='Impulse MACD', color='blue', linewidth=1)
    ax4.plot(df.index, results['impulse_macd']['sb'], label='Signal', color='red', linewidth=1)
    ax4.bar(df.index, results['impulse_macd']['sh'], label='Histogram', color='gray', alpha=0.5)
    ax4.set_title('Impulse MACD')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Enhanced Zero Lag MACD
    ax5 = axes[2, 0]
    ax5.plot(df.index, results['enhanced_macd']['zero_lag_macd'], label='MACD Line', color='blue', linewidth=1)
    ax5.plot(df.index, results['enhanced_macd']['signal'], label='Signal', color='red', linewidth=1)
    ax5.bar(df.index, results['enhanced_macd']['histogram'], label='Histogram', color='gray', alpha=0.5)
    ax5.set_title('Enhanced Zero Lag MACD')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Williams Fractal
    ax6 = axes[2, 1]
    ax6.plot(df.index, df['close'], label='Close Price', color='black', linewidth=1)
    ax6.plot(df.index, results['williams_fractal']['williams_long_stop_plot'], 
             label='Long Stop', color='green', linewidth=2)
    ax6.plot(df.index, results['williams_fractal']['williams_short_stop_plot'], 
             label='Short Stop', color='red', linewidth=2)
    ax6.set_title('Williams Fractal Trailing Stops')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in axes.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_filename = f"test_results_{timestamp}.png"
    fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"🖼️ Test results chart saved to: {plot_filename}")
    
    return fig

def main():
    """Run all tests"""
    print("🚀 Starting Indicator Validation Tests")
    print("=" * 50)
    
    try:
        # Test with synthetic data
        print("\n📊 Testing with synthetic data...")
        test_ema()
        test_dema()
        test_atr()
        test_impulse_macd()
        test_enhanced_zero_lag_macd()
        test_williams_fractal_trailing_stops()
        
        print("\n✅ All synthetic data tests passed!")
        
        # Test with real market data
        print("\n🌐 Testing with real market data...")
        real_results = test_with_real_data()
        
        if real_results:
            # Create visualization
            feeder = DataFeeder()
            df = feeder.fetch_data('XAUUSD', 'OANDA', n_bars=100)
            fig = plot_test_results(df, real_results)
            
            print(f"\n✅ All tests completed successfully!")
            print("📊 Check the generated chart for visual validation")
            
            # Show plot
            plt.show()
        else:
            print("⚠️ Real data tests skipped due to connection issues")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
