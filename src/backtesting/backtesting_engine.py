"""
Backtesting engine for trading strategies.
"""
import pandas as pd
from typing import Optional
from datetime import datetime

from ..strategies.base_strategy import BaseStrategy
from ..database.queries import get_combined_data
from .portfolio import Portfolio
from .performance_metrics import PerformanceMetrics


class BacktestEngine:
    """
    Backtesting engine that runs strategies on historical data.
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        starting_capital: float = 10000,
        commission_pct: float = 0.001
    ):
        """
        Initialize backtest engine.
        
        Args:
            strategy: Trading strategy to backtest
            starting_capital: Initial portfolio value
            commission_pct: Commission per trade (0.001 = 0.1%)
        """
        self.strategy = strategy
        self.starting_capital = starting_capital
        self.commission_pct = commission_pct
        
        # Results storage
        self.portfolio: Optional[Portfolio] = None
        self.results_df: Optional[pd.DataFrame] = None
        self.metrics: Optional[dict] = None
    
    def run(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> 'BacktestEngine':
        """
        Run backtest on historical data.
        
        Args:
            ticker: Ticker symbol to backtest
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Self (for method chaining)
        """
        print(f"\nRunning backtest: {self.strategy.name} on {ticker}")
        print(f"{'='*60}")
        
        # 1. Load data with indicators
        df = get_combined_data(ticker, start_date, end_date)
        
        if df.empty:
            raise ValueError(f"No data found for {ticker}")
        
        print(f"Loaded {len(df)} days of data ({df.index[0].date()} to {df.index[-1].date()})")
        
        # 2. Generate signals
        df = self.strategy.generate_signals(df)
        print(f"Generated signals: {(df['signal'] == 'BUY').sum()} BUYs, {(df['signal'] == 'SELL').sum()} SELLs")
        
        # 3. Initialize portfolio
        self.portfolio = Portfolio(
            starting_capital=self.starting_capital,
            commission_pct=self.commission_pct
        )
        
        # 4. Simulate trading
        for date, row in df.iterrows():
            signal = row['signal']
            price = row['close_price']
            
            if signal == 'BUY' and not self.portfolio.has_position():
                self.portfolio.buy(date, price)
            
            elif signal == 'SELL' and self.portfolio.has_position():
                self.portfolio.sell(date, price)
            
            # Record daily state
            self.portfolio.record_day(date, price)
        
        # 5. Close any open position at end
        if self.portfolio.has_position():
            last_date = df.index[-1]
            last_price = df.iloc[-1]['close_price']
            self.portfolio.sell(last_date, last_price)
        
        # 6. Calculate performance metrics
        self.results_df = df.copy()
        self.results_df['portfolio_value'] = [d['portfolio_value'] for d in self.portfolio.equity_curve]
        
        equity_series = pd.Series(
            [d['portfolio_value'] for d in self.portfolio.equity_curve],
            index=df.index
        )
        
        self.metrics = PerformanceMetrics.calculate_all(
            equity_curve=equity_series,
            starting_capital=self.starting_capital,
            trades=self.portfolio.get_closed_trades()
        )
        
        # Print summary
        self._print_summary()
        
        return self
    
    def _print_summary(self):
        """Print backtest results summary."""
        if not self.metrics:
            return
        
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS")
        print(f"{'='*60}")
        print(f"Strategy: {self.strategy.name}")
        print(f"\nPerformance:")
        print(f"  Starting Capital:    ${self.metrics['starting_capital']:,.2f}")
        print(f"  Final Value:         ${self.metrics['final_value']:,.2f}")
        print(f"  Total Return:        {self.metrics['total_return_pct']:.2f}%")
        print(f"  Annualized Return:   {self.metrics['annualized_return_pct']:.2f}%")
        print(f"\nRisk Metrics:")
        print(f"  Sharpe Ratio:        {self.metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown:        {self.metrics['max_drawdown_pct']:.2f}%")
        print(f"  Volatility:          {self.metrics['volatility']:.2f}%")
        print(f"\nTrading Stats:")
        print(f"  Total Trades:        {self.metrics['total_trades']}")
        print(f"  Winning Trades:      {self.metrics['winning_trades']}")
        print(f"  Losing Trades:       {self.metrics['losing_trades']}")
        print(f"  Win Rate:            {self.metrics['win_rate_pct']:.1f}%")
        print(f"  Avg Win:             {self.metrics['avg_win_pct']:.2f}%")
        print(f"  Avg Loss:            {self.metrics['avg_loss_pct']:.2f}%")
        print(f"  Profit Factor:       {self.metrics['profit_factor']:.2f}")
        print(f"  Avg Holding Days:    {self.metrics['avg_holding_days']:.1f}")
        print(f"{'='*60}\n")
    
    def get_results_df(self) -> pd.DataFrame:
        """
        Get DataFrame with backtest results.
        
        Returns:
            DataFrame with prices, signals, and portfolio values
        """
        if self.results_df is None:
            raise ValueError("Must run backtest first")
        return self.results_df
    
    def get_metrics(self) -> dict:
        """
        Get performance metrics dictionary.
        
        Returns:
            Dictionary of performance metrics
        """
        if self.metrics is None:
            raise ValueError("Must run backtest first")
        return self.metrics
    
    def get_trades_df(self) -> pd.DataFrame:
        """
        Get DataFrame of all trades.
        
        Returns:
            DataFrame with trade details
        """
        if self.portfolio is None:
            raise ValueError("Must run backtest first")
        
        trades = self.portfolio.get_closed_trades()
        
        return pd.DataFrame([
            {
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'shares': t.shares,
                'return_pct': t.return_pct,
                'return_dollars': t.return_dollars,
                'holding_days': t.holding_days
            }
            for t in trades
        ])


if __name__ == "__main__":
    # Test the backtest engine
    from ..strategies.sma_crossover import SMACrossover
    
    print("Testing Backtest Engine...")
    
    strategy = SMACrossover(short_window=5, long_window=20)
    engine = BacktestEngine(strategy, starting_capital=10000)
    
    # Run backtest (requires database with data)
    try:
        engine.run('AAPL')
        
        # Get trades
        trades = engine.get_trades_df()
        print("\nTrades executed:")
        print(trades)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure database has price and indicator data first!")
