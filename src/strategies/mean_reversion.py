"""
Bollinger Bands Mean Reversion Strategy.

Buy at lower Bollinger Band (oversold).
Sell at upper Bollinger Band (overbought).
"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class BollingerMeanReversion(BaseStrategy):
    """
    Bollinger Bands Mean Reversion Strategy.
    
    Assumes prices revert to the mean after extreme moves. Buys when price
    touches the lower band (oversold) and sells when price touches the
    upper band (overbought).
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        """
        Initialize Bollinger Mean Reversion Strategy.
        
        Args:
            window: Moving average window for Bollinger Bands (default 20)
            num_std: Number of standard deviations for bands (default 2)
        """
        parameters = {
            "window": window,
            "num_std": num_std
        }
        
        super().__init__(
            name="Bollinger Mean Reversion",
            strategy_type="Mean Reversion",
            parameters=parameters
        )
        
        self.window = window
        self.num_std = num_std
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return [
            'close_price',
            'bollinger_upper',
            'bollinger_middle',
            'bollinger_lower'
        ]
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            df: DataFrame with price data and Bollinger Bands
            
        Returns:
            DataFrame with 'signal' column added
        """
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # Initialize signal column
        df['signal'] = 'HOLD'
        
        # Calculate position relative to bands
        df['band_position'] = (
            (df['close_price'] - df['bollinger_lower']) / 
            (df['bollinger_upper'] - df['bollinger_lower'])
        )
        
        # BUY: Price at or below lower band (oversold)
        # We use <= 0.1 to catch touches near the lower band
        oversold = df['band_position'] <= 0.1
        df.loc[oversold, 'signal'] = 'BUY'
        
        # SELL: Price at or above upper band (overbought)
        # We use >= 0.9 to catch touches near the upper band
        overbought = df['band_position'] >= 0.9
        df.loc[overbought, 'signal'] = 'SELL'
        
        # Alternative approach: track crossings
        # BUY when price crosses above lower band from below
        prev_below_lower = df['close_price'].shift(1) < df['bollinger_lower'].shift(1)
        now_above_lower = df['close_price'] >= df['bollinger_lower']
        crosses_up = prev_below_lower & now_above_lower
        df.loc[crosses_up, 'signal'] = 'BUY'
        
        # SELL when price crosses below upper band from above
        prev_above_upper = df['close_price'].shift(1) > df['bollinger_upper'].shift(1)
        now_below_upper = df['close_price'] <= df['bollinger_upper']
        crosses_down = prev_above_upper & now_below_upper
        df.loc[crosses_down, 'signal'] = 'SELL'
        
        # Initial position: stay flat until first signal
        first_valid_idx = df[['close_price', 'bollinger_lower', 'bollinger_upper']].first_valid_index()
        if first_valid_idx is not None:
            # Start in cash, wait for first BUY signal
            if df.loc[first_valid_idx, 'band_position'] <= 0.1:
                df.loc[first_valid_idx, 'signal'] = 'BUY'
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"{self.name}: Buy when price touches lower Bollinger Band "
            f"({self.window}-day, {self.num_std} SD), sell at upper band "
            f"(mean reversion assumption)."
        )


if __name__ == "__main__":
    # Test the strategy
    print("Testing Bollinger Mean Reversion Strategy...")
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulate mean-reverting price
    price = 100 + np.random.randn(100).cumsum() * 0.5
    
    sample_df = pd.DataFrame({
        'close_price': price
    }, index=dates)
    
    # Calculate Bollinger Bands
    window = 20
    sample_df['bollinger_middle'] = sample_df['close_price'].rolling(window).mean()
    rolling_std = sample_df['close_price'].rolling(window).std()
    sample_df['bollinger_upper'] = sample_df['bollinger_middle'] + (rolling_std * 2)
    sample_df['bollinger_lower'] = sample_df['bollinger_middle'] - (rolling_std * 2)
    
    strategy = BollingerMeanReversion(window=20, num_std=2.0)
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nSignals generated:")
    signals = result_df[result_df['signal'].isin(['BUY', 'SELL'])]
    if not signals.empty:
        print(signals[['close_price', 'bollinger_lower', 'bollinger_middle', 'bollinger_upper', 'band_position', 'signal']].head(10))
    else:
        print("No signals generated")
    
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
