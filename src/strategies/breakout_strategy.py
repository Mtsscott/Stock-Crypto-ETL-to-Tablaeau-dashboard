"""
Breakout Strategy - Momentum-based trading.

Buy when price breaks significantly above moving average.
Sell when price breaks below moving average.
"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class BreakoutStrategy(BaseStrategy):
    """
    Breakout Strategy.
    
    Buys when price exceeds the moving average by a threshold percentage,
    indicating strong upward momentum. Sells when price falls below the
    moving average by the same threshold.
    """
    
    def __init__(self, window: int = 60, threshold_pct: float = 2.0):
        """
        Initialize Breakout Strategy.
        
        Args:
            window: Moving average window (default 60 days)
            threshold_pct: Percentage above/below MA to trigger signal (default 2%)
        """
        parameters = {
            "window": window,
            "threshold_pct": threshold_pct
        }
        
        super().__init__(
            name=f"Breakout ({window}-day)",
            strategy_type="Momentum",
            parameters=parameters
        )
        
        self.window = window
        self.threshold_pct = threshold_pct
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return [
            'close_price',
            f'sma_{self.window}'
        ]
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on price breakout.
        
        Args:
            df: DataFrame with price data and moving average
            
        Returns:
            DataFrame with 'signal' column added
        """
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # Get the SMA column
        sma_col = f'sma_{self.window}'
        
        # Calculate percentage difference from SMA
        df['price_vs_sma_pct'] = ((df['close_price'] - df[sma_col]) / df[sma_col]) * 100
        
        # Initialize signal column
        df['signal'] = 'HOLD'
        
        # BUY: Price breaks above SMA by threshold
        breakout_up = df['price_vs_sma_pct'] > self.threshold_pct
        df.loc[breakout_up, 'signal'] = 'BUY'
        
        # SELL: Price breaks below SMA by threshold
        breakout_down = df['price_vs_sma_pct'] < -self.threshold_pct
        df.loc[breakout_down, 'signal'] = 'SELL'
        
        # Initial position: if price is above threshold at start, buy
        first_valid_idx = df[[sma_col, 'price_vs_sma_pct']].first_valid_index()
        if first_valid_idx is not None:
            if df.loc[first_valid_idx, 'price_vs_sma_pct'] > self.threshold_pct:
                df.loc[first_valid_idx, 'signal'] = 'BUY'
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"{self.name}: Buy when price breaks {self.threshold_pct}% above "
            f"{self.window}-day MA, sell when it breaks {self.threshold_pct}% below."
        )


if __name__ == "__main__":
    # Test the strategy
    print("Testing Breakout Strategy...")
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulate price with breakouts
    price = 100 + np.random.randn(100).cumsum()
    
    sample_df = pd.DataFrame({
        'close_price': price,
        'sma_60': pd.Series(price).rolling(60).mean()
    }, index=dates)
    
    strategy = BreakoutStrategy(window=60, threshold_pct=2.0)
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nSignals generated:")
    signals = result_df[result_df['signal'].isin(['BUY', 'SELL'])]
    if not signals.empty:
        print(signals[['close_price', 'sma_60', 'price_vs_sma_pct', 'signal']])
    else:
        print("No BUY/SELL signals generated (price stayed within threshold)")
    
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
