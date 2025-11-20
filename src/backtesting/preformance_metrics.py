"""
Performance metrics calculations for backtesting.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from .portfolio import Trade


class PerformanceMetrics:
    """Calculate performance metrics for trading strategies."""
    
    @staticmethod
    def calculate_total_return(equity_curve: pd.Series, starting_capital: float) -> float:
        """
        Calculate total return percentage.
        
        Args:
            equity_curve: Series of portfolio values over time
            starting_capital: Initial capital
            
        Returns:
            Total return as percentage
        """
        final_value = equity_curve.iloc[-1]
        return ((final_value - starting_capital) / starting_capital) * 100
    
    @staticmethod
    def calculate_annualized_return(
        total_return_pct: float,
        num_days: int
    ) -> float:
        """
        Calculate annualized return.
        
        Args:
            total_return_pct: Total return percentage
            num_days: Number of days in backtest period
            
        Returns:
            Annualized return percentage
        """
        years = num_days / 365.25
        if years == 0:
            return 0
        
        # Compound annual growth rate
        return (((1 + total_return_pct / 100) ** (1 / years)) - 1) * 100
    
    @staticmethod
    def calculate_sharpe_ratio(
        equity_curve: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return).
        
        Args:
            equity_curve: Series of portfolio values
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        # Calculate daily returns
        daily_returns = equity_curve.pct_change().dropna()
        
        if len(daily_returns) == 0 or daily_returns.std() == 0:
            return 0
        
        # Annualize
        avg_return = daily_returns.mean() * 252  # 252 trading days
        std_return = daily_returns.std() * np.sqrt(252)
        
        # Sharpe = (Return - RiskFreeRate) / Volatility
        sharpe = (avg_return - risk_free_rate) / std_return
        
        return sharpe
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Maximum drawdown as percentage (negative value)
        """
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown from peak
        drawdown = (equity_curve - running_max) / running_max * 100
        
        # Return the maximum (most negative) drawdown
        max_dd = drawdown.min()
        
        return max_dd if not np.isnan(max_dd) else 0
    
    @staticmethod
    def calculate_volatility(equity_curve: pd.Series) -> float:
        """
        Calculate annualized volatility.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Annualized volatility as percentage
        """
        daily_returns = equity_curve.pct_change().dropna()
        
        if len(daily_returns) == 0:
            return 0
        
        # Annualize the standard deviation
        return daily_returns.std() * np.sqrt(252) * 100
    
    @staticmethod
    def calculate_trade_statistics(trades: List[Trade]) -> Dict:
        """
        Calculate trade-level statistics.
        
        Args:
            trades: List of closed trades
            
        Returns:
            Dictionary with trade statistics
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0,
                'avg_win_pct': 0,
                'avg_loss_pct': 0,
                'profit_factor': 0,
                'avg_holding_days': 0
            }
        
        winning_trades = [t for t in trades if t.return_pct and t.return_pct > 0]
        losing_trades = [t for t in trades if t.return_pct and t.return_pct <= 0]
        
        # Win rate
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        
        # Average win/loss
        avg_win = sum(t.return_pct for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.return_pct for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor (sum of wins / sum of losses)
        total_wins = sum(t.return_dollars for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t.return_dollars for t in losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Average holding period
        avg_days = sum(t.holding_days for t in trades) / len(trades) if trades else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': profit_factor,
            'avg_holding_days': avg_days
        }
    
    @classmethod
    def calculate_all(
        cls,
        equity_curve: pd.Series,
        starting_capital: float,
        trades: List[Trade],
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Calculate all performance metrics.
        
        Args:
            equity_curve: Series of portfolio values over time
            starting_capital: Initial capital
            trades: List of closed trades
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary with all metrics
        """
        final_value = equity_curve.iloc[-1]
        total_return_pct = cls.calculate_total_return(equity_curve, starting_capital)
        num_days = len(equity_curve)
        
        # Combine all metrics
        metrics = {
            'starting_capital': starting_capital,
            'final_value': final_value,
            'total_return_pct': total_return_pct,
            'annualized_return_pct': cls.calculate_annualized_return(total_return_pct, num_days),
            'sharpe_ratio': cls.calculate_sharpe_ratio(equity_curve, risk_free_rate),
            'max_drawdown_pct': cls.calculate_max_drawdown(equity_curve),
            'volatility': cls.calculate_volatility(equity_curve),
            'num_days': num_days
        }
        
        # Add trade statistics
        trade_stats = cls.calculate_trade_statistics(trades)
        metrics.update(trade_stats)
        
        return metrics


if __name__ == "__main__":
    # Test performance metrics
    print("Testing Performance Metrics...")
    
    # Create sample equity curve
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    
    # Simulate a portfolio that goes up 20% over the year with some volatility
    np.random.seed(42)
    returns = np.random.randn(252) * 0.01 + 0.0007  # ~20% annual return
    equity = 10000 * (1 + returns).cumprod()
    equity_curve = pd.Series(equity, index=dates)
    
    # Calculate metrics
    metrics = PerformanceMetrics.calculate_all(
        equity_curve=equity_curve,
        starting_capital=10000,
        trades=[],  # No trades for this test
        risk_free_rate=0.02
    )
    
    print("\nMetrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
