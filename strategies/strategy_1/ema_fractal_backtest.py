import pandas as pd
import mplfinance as mpf
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

pd.set_option('future.no_silent_downcasting', True)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from indicators.ema import calculate_ema
from indicators.williams_fractal_trailing_stops import williams_fractal_trailing_stops
from data_feeder.data_feeder import DataFeeder

def load_and_prepare_data(symbol, start_date, end_date, timeframe):
    """Load and prepare data using DataFeeder"""
    timeframe_map = {
        'M1': 1,
        'M5': 5,
        'M15': 15,
        'M30': 30,
        'H1': 60,
        'H4': 240,
        'D1': 1440,
    }
    interval_minutes = timeframe_map.get(timeframe, 60)
    
    feeder = DataFeeder()
    df = feeder.get_data(symbol, start_date, end_date, interval_minutes=interval_minutes, n_bars=5000)
    
    if df is None or df.empty:
        print("No data received from feeder")
        return None
    
    df.columns = df.columns.str.lower()
    
    if 'datetime' in df.columns:
        df.set_index('datetime', inplace=True)
    
    df = df.sort_index()
    return df

def add_ema(df, period=200, price_col='close'):
    ema_col = f'ema_{period}'
    df[ema_col] = calculate_ema(df[price_col], period)
    return df, ema_col

def calculate_strategy_positions(df, ema_col='ema_200', breakout_threshold=0.5):
    positions = []
    open_positions = 0
    entry_signal = False
    reference_high = None
    reference_low = None
    entry_candles = []
    exit_candles = []

    for i in range(len(df)):
        open_i = df['open'].iloc[i]
        close_i = df['close'].iloc[i]
        high_i = df['high'].iloc[i]
        low_i = df['low'].iloc[i]
        ema_i = df[ema_col].iloc[i]
        ema200_i = df['ema_200'].iloc[i]
        current_pos = open_positions

        if close_i < ema_i:
            reference_high = None
            reference_low = None

        if close_i > ema200_i:
            if not pd.isna(df['williams_high_price'].iloc[i]) and low_i > ema_i:
                reference_high = df['high'].iloc[i]
                reference_low = df['low'].iloc[i]

            if reference_high is not None:
                body = abs(close_i - open_i)
                if body > 0:
                    top = max(open_i, close_i)
                    bot = min(open_i, close_i)
                    if top <= reference_high:
                        body_above = 0
                    elif bot >= reference_high:
                        body_above = body
                    else:
                        body_above = top - reference_high
                    if body_above >= breakout_threshold * body:
                        entry_signal = True

        if entry_signal:
            open_positions += 1
            entry_candles.append(df.index[i])
            entry_signal = False
            current_pos = open_positions

        if open_positions > 0 and close_i < ema_i:
            exit_candles.append(df.index[i])
            open_positions = 0
            current_pos = 0

        positions.append(current_pos)

    assert len(positions) == len(df)
    df['strategy_position'] = pd.Series(positions, index=df.index).astype(int)
    df['entry_signal'] = 0
    df['exit_signal'] = 0
    df.loc[entry_candles, 'entry_signal'] = 1
    df.loc[exit_candles, 'exit_signal'] = 1
    return df

def calculate_performance_metrics(df, initial_capital=10000):
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['strategy_position'].shift(1) * df['returns']
    df['cumulative_returns'] = (1 + df['returns']).cumprod()
    df['strategy_cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    df['equity'] = initial_capital * df['strategy_cumulative_returns']
    df['peak'] = df['equity'].expanding().max()
    df['drawdown'] = (df['equity'] - df['peak']) / df['peak']
    
    total_return = (df['equity'].iloc[-1] - initial_capital) / initial_capital
    annualized_return = total_return * (252 / len(df))
    volatility = df['strategy_returns'].std() * np.sqrt(252)
    sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
    max_drawdown = df['drawdown'].min()
    
    trades = df[df['entry_signal'] == 1].copy()
    if len(trades) > 0:
        trade_results = []
        for i, entry_idx in enumerate(trades.index):
            exit_mask = (df.index > entry_idx) & (df['exit_signal'] == 1)
            if exit_mask.any():
                exit_idx = df[exit_mask].index[0]
                entry_price = df.loc[entry_idx, 'close']
                exit_price = df.loc[exit_idx, 'close']
                trade_return = (exit_price - entry_price) / entry_price
                trade_results.append(trade_return)
        
        if trade_results:
            win_rate = sum(1 for r in trade_results if r > 0) / len(trade_results)
            avg_win = np.mean([r for r in trade_results if r > 0]) if any(r > 0 for r in trade_results) else 0
            avg_loss = np.mean([r for r in trade_results if r < 0]) if any(r < 0 for r in trade_results) else 0
            profit_factor = abs(sum([r for r in trade_results if r > 0]) / sum([r for r in trade_results if r < 0])) if sum([r for r in trade_results if r < 0]) != 0 else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
    else:
        win_rate = avg_win = avg_loss = profit_factor = 0
    
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
    negative_returns = df['strategy_returns'][df['strategy_returns'] < 0]
    downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
    sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0
    
    metrics = {
        'Total Return (%)': total_return * 100,
        'Annualized Return (%)': annualized_return * 100,
        'Volatility (%)': volatility * 100,
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        'Calmar Ratio': calmar_ratio,
        'Max Drawdown (%)': max_drawdown * 100,
        'Win Rate (%)': win_rate * 100,
        'Average Win (%)': avg_win * 100,
        'Average Loss (%)': avg_loss * 100,
        'Profit Factor': profit_factor,
        'Total Trades': len(trades),
        'Initial Capital': initial_capital,
        'Final Equity': df['equity'].iloc[-1]
    }
    return metrics, df

def plot_strategy(df, symbol):
    ema_col = 'ema_200'
    ema_plot = mpf.make_addplot(df[ema_col], color='blue', width=1)
    position_plot = mpf.make_addplot(df['strategy_position'], color='orange', ylabel='Positions', panel=1)
    
    entry_markers = pd.Series(np.nan, index=df.index)
    entry_markers[df['entry_signal'] == 1] = df.loc[df['entry_signal'] == 1, 'low'] * 0.995
    entry_plot = mpf.make_addplot(entry_markers, type='scatter', markersize=100, marker='^', color='lime')
    
    exit_markers = pd.Series(np.nan, index=df.index)
    exit_markers[df['exit_signal'] == 1] = df.loc[df['exit_signal'] == 1, 'high'] * 1.005
    exit_plot = mpf.make_addplot(exit_markers, type='scatter', markersize=100, marker='v', color='red')
    
    high_fractals = df['williams_high_price'].copy()
    low_fractals = df['williams_low_price'].copy()
    high_fractals = high_fractals.where(df['is_williams_high'], other=pd.NA)
    low_fractals = low_fractals.where(df['is_williams_low'], other=pd.NA)
    high_fractals = high_fractals.astype(float)
    low_fractals = low_fractals.astype(float)
    
    high_fractal_plot = mpf.make_addplot(high_fractals, type='scatter', markersize=80, marker='v', color='red', alpha=0.7)
    low_fractal_plot = mpf.make_addplot(low_fractals, type='scatter', markersize=80, marker='^', color='green', alpha=0.7)
    
    addplots = [ema_plot, entry_plot, exit_plot, high_fractal_plot, low_fractal_plot, position_plot]
    
    mpf.plot(
        df,
        type='candle',
        style='charles',
        addplot=addplots,
        title=f"{symbol} - EMA + Williams Fractal Strategy Backtest Results",
        ylabel='Price',
        volume=True,
        figsize=(12,8)
    )

def main():
    SYMBOL = "XAUUSD"
    START_DATE = "2025-08-01"
    END_DATE = "2025-08-20"
    EMA_PERIOD = 200
    BREAKOUT_THRESHOLD = 0.5
    WILLIAMS_LEFT_RANGE = 9
    WILLIAMS_RIGHT_RANGE = 9
    INITIAL_CAPITAL = 10000
    PLOT_STRATEGY = False  # Set to True to enable plotting
    PRINT_METRICS = True
    
    print("🚀 Starting EMA + Williams Fractal Strategy Backtest")
    print("=" * 60)
    print(f"Symbol: {SYMBOL}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"EMA Period: {EMA_PERIOD}")
    print(f"Breakout Threshold: {BREAKOUT_THRESHOLD * 100}%")
    print(f"Williams Fractal Range: {WILLIAMS_LEFT_RANGE}L/{WILLIAMS_RIGHT_RANGE}R")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print("=" * 60)
    
    try:
        print("📊 Loading and preparing data...")
        df = load_and_prepare_data(symbol=SYMBOL, start_date=START_DATE, end_date=END_DATE, timeframe="H1")
        
        if df is None or df.empty:
            print("❌ No data loaded")
            return
        
        print(f"✅ Loaded {len(df)} bars of data")
        print(f"📅 Data range: {df.index.min()} to {df.index.max()}")
        

        
        print("🧮 Calculating technical indicators...")
        df, ema_col = add_ema(df, period=EMA_PERIOD, price_col='close')
        
        wft_df = williams_fractal_trailing_stops(df, left_range=WILLIAMS_LEFT_RANGE, right_range=WILLIAMS_RIGHT_RANGE, buffer_percent=0.5, flip_on="Close")
        df = df.join(wft_df)
        
        print("📈 Calculating strategy positions...")
        df = calculate_strategy_positions(df, ema_col=ema_col, breakout_threshold=BREAKOUT_THRESHOLD)
        
        print("📊 Calculating performance metrics...")
        metrics, _ = calculate_performance_metrics(df, initial_capital=INITIAL_CAPITAL)
        
        if PRINT_METRICS:
            print("\n" + "=" * 60)
            print("📊 STRATEGY PERFORMANCE SUMMARY")
            print("=" * 60)
            
            for key, value in metrics.items():
                if 'Ratio' in key or 'Factor' in key:
                    print(f"{key:<25}: {value:>8.4f}")
                elif 'Return' in key or 'Drawdown' in key or 'Win Rate' in key or 'Win' in key or 'Loss' in key:
                    print(f"{key:<25}: {value:>8.2f}%")
                elif 'Capital' in key or 'Equity' in key:
                    print(f"{key:<25}: ${value:>8,.2f}")
                else:
                    print(f"{key:<25}: {value:>8}")
        
        total_positions = df['strategy_position'].max() if df['strategy_position'].max() > 0 else 0
        entry_signals = df['entry_signal'].sum()
        exit_signals = df['exit_signal'].sum()
        neutral_positions = (df['strategy_position'] == 0).sum()
        
        print(f"\n📈 Strategy Summary:")
        print(f"   Max Positions: {total_positions}")
        print(f"   Entry Signals: {entry_signals}")
        print(f"   Exit Signals: {exit_signals}")
        print(f"   Neutral Periods: {neutral_positions}")
        
        if PLOT_STRATEGY and len(df) > 0 and entry_signals > 0:
            print("\n🎨 Generating strategy visualization...")
            plot_strategy(df, SYMBOL)
        elif PLOT_STRATEGY and entry_signals == 0:
            print("\n⚠️  No trading signals generated - skipping visualization")
        
        print("\n✅ EMA + Williams Fractal Backtest completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during backtest: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
