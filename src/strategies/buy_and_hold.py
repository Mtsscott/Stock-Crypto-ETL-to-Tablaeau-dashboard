"""
Buy and Hold Strategy - Baseline for comparison.

Buy on the first day and hold forever.
"""
import pandas as pd
from .base_strategy import BaseStrategy


class BuyAndHold(BaseStrategy):
    """
    Buy and Hold Strategy.
    
    Simply buys on the first available day and holds the position indefinitely.
    This serves as a baseline to compare active trading strategies against.
    """
    
    def __init__(self):
        """Initialize Buy and Hold strategy."""
        parameters = {"action": "buy_first_day"}
        
        super().__init__(
            name="Buy and Hold",
            strategy_type="Baseline",
            parameters=parameters
        )
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return ['close_price']  # Only needs price data
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals: BUY on first day, HOLD thereafter.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            DataFrame with 'signal' column added
        """
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # All days are HOLD
        df['signal'] = 'HOLD'
        
        # First day is BUY
        df.iloc[0, df.columns.get_loc('signal')] = 'BUY'
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return "Buy and Hold: Purchase on first day and hold indefinitely (baseline strategy)"


if __name__ == "__main__":
    # Test the strategy
    import numpy as np
    
    print("Testing Buy and Hold Strategy...")
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    sample_df = pd.DataFrame({
        'close_price': 100 + np.random.randn(100).cumsum()
    }, index=dates)
    
    strategy = BuyAndHold()
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nFirst 10 signals:")
    print(result_df.head(10)[['close_price', 'signal']])
    
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
