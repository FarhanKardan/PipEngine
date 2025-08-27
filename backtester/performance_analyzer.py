"""
Performance Analyzer Module

This module calculates comprehensive performance metrics for backtesting results.
Includes drawdown analysis, risk metrics, and performance ratios.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PerformanceAnalyzer:
    """
    Performance Analyzer Class
    
    Calculates comprehensive performance metrics for trading strategies.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize the performance analyzer
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_metrics(self, trades: List[Dict], equity_curve: List[Dict], 
                         initial_capital: float) -> Dict:
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades: List of trade dictionaries
            equity_curve: List of equity curve data points
            initial_capital: Initial capital amount
            
        Returns:
            Dictionary containing all performance metrics
        """
        if not trades or not equity_curve:
            return {}
        
        # Convert to DataFrames for easier analysis
        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(equity_curve)
        
        # Basic metrics
        basic_metrics = self._calculate_basic_metrics(trades_df, equity_df, initial_capital)
        
        # Risk metrics
        risk_metrics = self._calculate_risk_metrics(equity_df, initial_capital)
        
        # Trade analysis
        trade_metrics = self._calculate_trade_metrics(trades_df)
        
        # Drawdown analysis
        drawdown_metrics = self._calculate_drawdown_metrics(equity_df)
        
        # Performance ratios
        performance_ratios = self._calculate_performance_ratios(
            basic_metrics, risk_metrics, equity_df, initial_capital
        )
        
        # Combine all metrics
        all_metrics = {
            **basic_metrics,
            **risk_metrics,
            **trade_metrics,
            **drawdown_metrics,
            **performance_ratios
        }
        
        return all_metrics
    
    def _calculate_basic_metrics(self, trades_df: pd.DataFrame, 
                                equity_df: pd.DataFrame, 
                                initial_capital: float) -> Dict:
        """Calculate basic performance metrics"""
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital * 100
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        equity_df['cumulative_returns'] = (1 + equity_df['returns']).cumprod()
        
        # Annualized return (assuming daily data)
        try:
            if isinstance(equity_df['time'].iloc[0], (int, np.integer)):
                # If time is integer index, assume it's bars and convert to days
                total_bars = equity_df['time'].iloc[-1] - equity_df['time'].iloc[0]
                total_days = total_bars / 1440  # Assuming M1 data (1440 bars per day)
            else:
                # If time is datetime, calculate actual days
                total_days = (equity_df['time'].iloc[-1] - equity_df['time'].iloc[0]).days
            
            if total_days > 0:
                annualized_return = ((final_equity / initial_capital) ** (365 / total_days) - 1) * 100
            else:
                annualized_return = 0
        except:
            # Fallback if time calculation fails
            total_days = 1
            annualized_return = 0
        
        return {
            'total_return': total_return,
            'final_equity': final_equity,
            'annualized_return': annualized_return,
            'total_days': total_days
        }
    
    def _calculate_risk_metrics(self, equity_df: pd.DataFrame, 
                               initial_capital: float) -> Dict:
        """Calculate risk metrics"""
        returns = equity_df['returns'].dropna()
        
        if len(returns) == 0:
            return {}
        
        # Volatility
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252) * 100
        
        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5) * 100
        var_99 = np.percentile(returns, 1) * 100
        
        # Maximum loss
        max_loss = returns.min() * 100
        
        return {
            'daily_volatility': daily_volatility * 100,
            'annualized_volatility': annualized_volatility,
            'var_95': var_95,
            'var_99': var_99,
            'max_loss': max_loss
        }
    
    def _calculate_trade_metrics(self, trades_df: pd.DataFrame) -> Dict:
        """Calculate trade-specific metrics"""
        if trades_df.empty:
            return {}
        
        # Filter completed trades
        completed_trades = trades_df[trades_df['exit_time'].notna()].copy()
        open_trades = trades_df[trades_df['exit_time'].isna()].copy()
        
        total_trades = len(trades_df)
        completed_trades_count = len(completed_trades)
        open_trades_count = len(open_trades)
        
        if completed_trades.empty:
            return {
                'total_trades': total_trades,
                'completed_trades': completed_trades_count,
                'open_trades': open_trades_count,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'avg_trade': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        # Win/loss analysis
        winning_trades = completed_trades[completed_trades['net_pnl'] > 0]
        losing_trades = completed_trades[completed_trades['net_pnl'] < 0]
        
        winning_trades_count = len(winning_trades)
        losing_trades_count = len(losing_trades)
        
        win_rate = (winning_trades_count / completed_trades_count * 100) if completed_trades_count > 0 else 0
        
        # P&L metrics
        total_pnl = completed_trades['net_pnl'].sum()
        avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
        
        # Profit factor
        gross_profit = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade
        avg_trade = completed_trades['net_pnl'].mean()
        
        # Largest win/loss
        largest_win = completed_trades['net_pnl'].max()
        largest_loss = completed_trades['net_pnl'].min()
        
        return {
            'total_trades': total_trades,
            'completed_trades': completed_trades_count,
            'open_trades': open_trades_count,
            'winning_trades': winning_trades_count,
            'losing_trades': losing_trades_count,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_trade': avg_trade,
            'largest_win': largest_win,
            'largest_loss': largest_loss
        }
    
    def _calculate_drawdown_metrics(self, equity_df: pd.DataFrame) -> Dict:
        """Calculate drawdown metrics"""
        equity = equity_df['equity'].values
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak * 100
        
        # Maximum drawdown
        max_drawdown = drawdown.min()
        
        # Current drawdown
        current_drawdown = drawdown[-1]
        
        # Drawdown duration
        drawdown_periods = []
        in_drawdown = False
        start_period = 0
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                start_period = i
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                drawdown_periods.append(i - start_period)
        
        # If still in drawdown at the end
        if in_drawdown:
            drawdown_periods.append(len(drawdown) - start_period)
        
        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0
        max_drawdown_duration = np.max(drawdown_periods) if drawdown_periods else 0
        
        return {
            'max_drawdown': max_drawdown,
            'current_drawdown': current_drawdown,
            'avg_drawdown_duration': avg_drawdown_duration,
            'max_drawdown_duration': max_drawdown_duration
        }
    
    def _calculate_performance_ratios(self, basic_metrics: Dict, risk_metrics: Dict,
                                    equity_df: pd.DataFrame, initial_capital: float) -> Dict:
        """Calculate performance ratios"""
        returns = equity_df['returns'].dropna()
        
        if len(returns) == 0:
            return {}
        
        # Sharpe Ratio
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # Sortino Ratio (using downside deviation)
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = (excess_returns.mean() / downside_deviation) * np.sqrt(252) if downside_deviation > 0 else 0
        
        # Calmar Ratio
        max_dd = abs(basic_metrics.get('max_drawdown', 0))
        calmar_ratio = basic_metrics.get('annualized_return', 0) / max_dd if max_dd > 0 else 0
        
        # Recovery Factor
        total_return = basic_metrics.get('total_return', 0)
        recovery_factor = abs(total_return / max_dd) if max_dd > 0 else 0
        
        # Risk-adjusted return
        risk_adjusted_return = basic_metrics.get('total_return', 0) / abs(max_dd) if max_dd > 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            'risk_adjusted_return': risk_adjusted_return
        }
    
    def generate_report(self, metrics: Dict) -> str:
        """
        Generate a formatted performance report
        
        Args:
            metrics: Dictionary of performance metrics
            
        Returns:
            Formatted report string
        """
        if not metrics:
            return "No metrics available for report generation."
        
        report = []
        report.append("=" * 80)
        report.append("📊 PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 80)
        
        # Basic Metrics
        report.append("\n💰 BASIC METRICS:")
        report.append(f"   Total Return: {metrics.get('total_return', 'N/A'):.2f}%")
        report.append(f"   Annualized Return: {metrics.get('annualized_return', 'N/A'):.2f}%")
        report.append(f"   Final Equity: ${metrics.get('final_equity', 'N/A'):,.2f}")
        
        # Risk Metrics
        report.append("\n⚠️  RISK METRICS:")
        report.append(f"   Max Drawdown: {metrics.get('max_drawdown', 'N/A'):.2f}%")
        report.append(f"   Annualized Volatility: {metrics.get('annualized_volatility', 'N/A'):.2f}%")
        report.append(f"   VaR (95%): {metrics.get('var_95', 'N/A'):.2f}%")
        report.append(f"   VaR (99%): {metrics.get('var_99', 'N/A'):.2f}%")
        
        # Trade Metrics
        report.append("\n📈 TRADE METRICS:")
        report.append(f"   Total Trades: {metrics.get('total_trades', 'N/A')}")
        report.append(f"   Win Rate: {metrics.get('win_rate', 'N/A'):.1f}%")
        report.append(f"   Profit Factor: {metrics.get('profit_factor', 'N/A'):.2f}")
        report.append(f"   Average Trade: ${metrics.get('avg_trade', 'N/A'):.2f}")
        
        # Performance Ratios
        report.append("\n📊 PERFORMANCE RATIOS:")
        report.append(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.3f}")
        report.append(f"   Sortino Ratio: {metrics.get('sortino_ratio', 'N/A'):.3f}")
        report.append(f"   Calmar Ratio: {metrics.get('calmar_ratio', 'N/A'):.3f}")
        report.append(f"   Recovery Factor: {metrics.get('recovery_factor', 'N/A'):.2f}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
