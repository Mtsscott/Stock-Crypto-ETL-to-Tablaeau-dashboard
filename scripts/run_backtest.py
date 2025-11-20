#!/usr/bin/env python3
"""
Run backtests for all strategies on all tickers.

Usage:
    python scripts/run_backtests.py
    python scripts/run_backtests.py --ticker AAPL            # Single ticker
    python scripts/run_backtests.py --strategy "Buy and Hold"  # Single strategy
"""
import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.sma_crossover import SMACrossover
from src.strategies.buy_and_hold import BuyAndHold
# Import other strategies as you create them
# from src.strategies.breakout_strategy import BreakoutStrategy
# from src.strategies.volatility_strategy import VolatilityBreakout
# from src.strategies.mean_reversion import BollingerMeanReversion
# from src.strategies.volume_momentum import VolumeMomentum

from src.database.queries import get_all_tickers
from src.database.connection import get_engine
from sqlalchemy import text


def get_all_strategies():
    """
    Define all strategies to backtest.
    
    Returns:
        List of strategy instances
    """
    return [
        BuyAndHold(),
        SMACrossover(short_window=5, long_window=20),
        # Add more strategies as you create them:
        # BreakoutStrategy(window=60, threshold=2.0),
        # VolatilityBreakout(sma_window=20, atr_window=14, atr_multiplier=1.5),
        # BollingerMeanReversion(window=20, num_std=2.0),
        # VolumeMomentum(volume_window=20, volume_multiplier=1.5)
    ]


def save_results_to_database(engine, ticker, strategy_name, metrics):
    """
    Save backtest results to database.
    
    Args:
        engine: SQLAlchemy engine
        ticker: Ticker symbol
        strategy_name: Strategy name
        metrics: Performance metrics dictionary
    """
    # Get IDs
    ticker_query = text("SELECT ticker_id FROM dim_ticker WHERE ticker_symbol = :ticker")
    strategy_query = text("SELECT strategy_id FROM dim_strategy WHERE strategy_name = :name")
    
    with engine.connect() as conn:
        ticker_id = conn.execute(ticker_query, {"ticker": ticker}).scalar()
        strategy_id = conn.execute(strategy_query, {"name": strategy_name}).scalar()
        
        if not ticker_id or not strategy_id:
            print(f"  ⚠ Could not find IDs for {ticker} / {strategy_name}")
            return
        
        # Check if record exists
        check_query = text("""
            SELECT summary_id FROM fact_strategy_summary 
            WHERE ticker_id = :tid AND strategy_id = :sid
        """)
        existing = conn.execute(
            check_query,
            {"tid": ticker_id, "sid": strategy_id}
        ).scalar()
        
        if existing:
            # Update existing record
            update_query = text("""
                UPDATE fact_strategy_summary
                SET final_portfolio_value = :final_value,
                    total_return_pct = :total_return,
                    annualized_return_pct = :annualized_return,
                    sharpe_ratio = :sharpe,
                    max_drawdown_pct = :max_dd,
                    volatility = :volatility,
                    total_trades = :total_trades,
                    winning_trades = :winning,
                    losing_trades = :losing,
                    win_rate_pct = :win_rate,
                    avg_win_pct = :avg_win,
                    avg_loss_pct = :avg_loss,
                    profit_factor = :profit_factor,
                    avg_holding_days = :avg_days,
                    calculated_at = GETDATE()
                WHERE ticker_id = :tid AND strategy_id = :sid
            """)
        else:
            # Insert new record
            update_query = text("""
                INSERT INTO fact_strategy_summary (
                    ticker_id, strategy_id,
                    final_portfolio_value, total_return_pct, annualized_return_pct,
                    sharpe_ratio, max_drawdown_pct, volatility,
                    total_trades, winning_trades, losing_trades,
                    win_rate_pct, avg_win_pct, avg_loss_pct,
                    profit_factor, avg_holding_days
                ) VALUES (
                    :tid, :sid,
                    :final_value, :total_return, :annualized_return,
                    :sharpe, :max_dd, :volatility,
                    :total_trades, :winning, :losing,
                    :win_rate, :avg_win, :avg_loss,
                    :profit_factor, :avg_days
                )
            """)
        
        conn.execute(update_query, {
            "tid": ticker_id,
            "sid": strategy_id,
            "final_value": metrics['final_value'],
            "total_return": metrics['total_return_pct'],
            "annualized_return": metrics['annualized_return_pct'],
            "sharpe": metrics['sharpe_ratio'],
            "max_dd": metrics['max_drawdown_pct'],
            "volatility": metrics['volatility'],
            "total_trades": metrics['total_trades'],
            "winning": metrics['winning_trades'],
            "losing": metrics['losing_trades'],
            "win_rate": metrics['win_rate_pct'],
            "avg_win": metrics['avg_win_pct'],
            "avg_loss": metrics['avg_loss_pct'],
            "profit_factor": metrics['profit_factor'],
            "avg_days": metrics['avg_holding_days']
        })
        conn.commit()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run strategy backtests')
    parser.add_argument('--ticker', type=str, help='Test single ticker')
    parser.add_argument('--strategy', type=str, help='Test single strategy')
    
    args = parser.parse_args()
    
    # Get tickers
    tickers_df = get_all_tickers()
    if args.ticker:
        tickers_df = tickers_df[tickers_df['ticker_symbol'] == args.ticker]
    
    tickers = tickers_df['ticker_symbol'].tolist()
    
    # Get strategies
    strategies = get_all_strategies()
    if args.strategy:
        strategies = [s for s in strategies if s.name == args.strategy]
    
    if not tickers or not strategies:
        print("No tickers or strategies to test!")
        return
    
    print(f"{'='*70}")
    print(f"Backtesting Framework")
    print(f"Tickers: {len(tickers)}")
    print(f"Strategies: {len(strategies)}")
    print(f"Total backtests: {len(tickers) * len(strategies)}")
    print(f"{'='*70}\n")
    
    # Get database engine
    engine = get_engine()
    
    # Results storage
    all_results = []
    
    # Run all combinations
    for ticker in tickers:
        for strategy in strategies:
            try:
                # Run backtest
                bt = BacktestEngine(strategy, starting_capital=10000, commission_pct=0.001)
                bt.run(ticker)
                
                # Get metrics
                metrics = bt.get_metrics()
                metrics['ticker'] = ticker
                metrics['strategy'] = strategy.name
                all_results.append(metrics)
                
                # Save to database
                save_results_to_database(engine, ticker, strategy.name, metrics)
                
            except Exception as e:
                print(f"  ✗ Error testing {strategy.name} on {ticker}: {e}\n")
    
    # Summary report
    print(f"\n{'='*70}")
    print(f"BACKTEST SUMMARY")
    print(f"{'='*70}\n")
    
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        # Best performing strategy per ticker
        print("Best Strategy by Ticker:")
        best_by_ticker = results_df.loc[results_df.groupby('ticker')['total_return_pct'].idxmax()]
        print(best_by_ticker[['ticker', 'strategy', 'total_return_pct', 'sharpe_ratio']].to_string(index=False))
        
        print("\n\nBest Performing Strategies Overall:")
        top_strategies = results_df.nlargest(10, 'sharpe_ratio')[
            ['ticker', 'strategy', 'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct']
        ]
        print(top_strategies.to_string(index=False))
    
    print(f"\n{'='*70}")
    print(f"Complete! Results saved to database.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
