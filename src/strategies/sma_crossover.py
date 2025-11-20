"""
Simple Moving Average (SMA) Crossover Strategy.

Buy when short-term SMA crosses above long-term SMA.
Sell when short-term SMA crosses below long-term SMA.
"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class SMACrossover(BaseStrategy):
    """
    SMA Crossover Strategy.
    
    Generates BUY signal when fast SMA crosses above slow SMA (golden cross).
    Generates SELL signal when fast SMA crosses below slow SMA (death cross).
    """
    
    def __init__(self, short_window: int = 5, long_window: int = 20):
        """
        Initialize SMA Crossover strategy.
        
        Args:
            short_window: Period for fast moving average (default 5)
            long_window: Period for slow moving average (default 20)
        """
        parameters = {
            "short_window": short_window,
            "long_window": long_window
        }
        
        super().__init__(
            name=f"SMA Crossover ({short_window}/{long_window})",
            strategy_type="Momentum",
            parameters=parameters
        )
        
        self.short_window = short_window
        self.long_window = long_window
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return [
            'close_price',
            f'sma_{self.short_window}',
            f'sma_{self.long_window}'
        ]
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on SMA crossover.
        
        Args:
            df: DataFrame with price data and SMAs
            
        Returns:
            DataFrame with 'signal' column added
        """
        # Validate required columns exist
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # Get the SMA columns
        short_sma = f'sma_{self.short_window}'
        long_sma = f'sma_{self.long_window}'
        
        # Initialize signal column
        df['signal'] = 'HOLD'
        
        # Detect crossovers
        # Golden Cross: short SMA crosses above long SMA (BUY)
        # Death Cross: short SMA crosses below long SMA (SELL)
        
        # Previous values
        short_above_long_prev = df[short_sma].shift(1) > df[long_sma].shift(1)
        short_above_long_now = df[short_sma] > df[long_sma]
        
        # Golden Cross: wasn't above before, but is now
        golden_cross = (~short_above_long_prev) & short_above_long_now
        df.loc[golden_cross, 'signal'] = 'BUY'
        
        # Death Cross: was above before, but isn't now
        death_cross = short_above_long_prev & (~short_above_long_now)
        df.loc[death_cross, 'signal'] = 'SELL'
        
        # For the first period where we have both SMAs, determine initial position
        # If short > long at start, we're in a bullish trend (BUY)
        # If short < long at start, stay out (HOLD/SELL)
        first_valid_idx = df[[short_sma, long_sma]].first_valid_index()
        if first_valid_idx is not None:
            if df.loc[first_valid_idx, short_sma] > df.loc[first_valid_idx, long_sma]:
                df.loc[first_valid_idx, 'signal'] = 'BUY'
        
        # Forward fill signals (maintain position until next signal)
        # But only for the strategy logic - let backtest engine handle position tracking
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"{self.name}: Buy when {self.short_window}-day SMA crosses above "
            f"{self.long_window}-day SMA, sell when it crosses below."
        )


if __name__ == "__main__":
    # Test the strategy with sample data
    print("Testing SMA Crossover Strategy...")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulate price data with trend
    price = 100 + np.random.randn(100).cumsum()
    
    sample_df = pd.DataFrame({
        'close_price': price,
        'sma_5': pd.Series(price).rolling(5).mean(),
        'sma_20': pd.Series(price).rolling(20).mean()
    }, index=dates)
    
    # Apply strategy
    strategy = SMACrossover(short_window=5, long_window=20)
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nSignals generated:")
    print(result_df[result_df['signal'].isin(['BUY', 'SELL'])][['close_price', 'sma_5', 'sma_20', 'signal']])
    
    # Summary
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
