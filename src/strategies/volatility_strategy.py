"""
ATR Volatility Breakout Strategy.

Buy when price exceeds SMA + ATR threshold (expanding volatility).
Sell when price falls below SMA - ATR threshold.
"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class VolatilityBreakout(BaseStrategy):
    """
    ATR-based Volatility Breakout Strategy.
    
    Uses Average True Range (ATR) to identify breakouts that account for
    current market volatility. More volatile markets require larger price
    moves to trigger signals.
    """
    
    def __init__(
        self, 
        sma_window: int = 20, 
        atr_window: int = 14, 
        atr_multiplier: float = 1.5
    ):
        """
        Initialize Volatility Breakout Strategy.
        
        Args:
            sma_window: Moving average window (default 20)
            atr_window: ATR calculation period (default 14)
            atr_multiplier: ATR multiplier for threshold (default 1.5)
        """
        parameters = {
            "sma_window": sma_window,
            "atr_window": atr_window,
            "atr_multiplier": atr_multiplier
        }
        
        super().__init__(
            name="ATR Volatility Breakout",
            strategy_type="Volatility",
            parameters=parameters
        )
        
        self.sma_window = sma_window
        self.atr_window = atr_window
        self.atr_multiplier = atr_multiplier
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return [
            'close_price',
            f'sma_{self.sma_window}',
            f'atr_{self.atr_window}'
        ]
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on volatility-adjusted breakouts.
        
        Args:
            df: DataFrame with price data, SMA, and ATR
            
        Returns:
            DataFrame with 'signal' column added
        """
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # Get the indicator columns
        sma_col = f'sma_{self.sma_window}'
        atr_col = f'atr_{self.atr_window}'
        
        # Calculate dynamic thresholds based on volatility
        df['upper_threshold'] = df[sma_col] + (df[atr_col] * self.atr_multiplier)
        df['lower_threshold'] = df[sma_col] - (df[atr_col] * self.atr_multiplier)
        
        # Initialize signal column
        df['signal'] = 'HOLD'
        
        # BUY: Price breaks above upper threshold
        breakout_up = df['close_price'] > df['upper_threshold']
        df.loc[breakout_up, 'signal'] = 'BUY'
        
        # SELL: Price breaks below lower threshold
        breakout_down = df['close_price'] < df['lower_threshold']
        df.loc[breakout_down, 'signal'] = 'SELL'
        
        # Initial position
        first_valid_idx = df[['close_price', 'upper_threshold']].first_valid_index()
        if first_valid_idx is not None:
            if df.loc[first_valid_idx, 'close_price'] > df.loc[first_valid_idx, 'upper_threshold']:
                df.loc[first_valid_idx, 'signal'] = 'BUY'
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"{self.name}: Buy when price exceeds {self.sma_window}-day SMA + "
            f"{self.atr_multiplier}x ATR({self.atr_window}), sell when below SMA - "
            f"{self.atr_multiplier}x ATR."
        )


if __name__ == "__main__":
    # Test the strategy
    print("Testing Volatility Breakout Strategy...")
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulate price with varying volatility
    price = 100 + np.random.randn(100).cumsum()
    high = price + np.random.rand(100) * 2
    low = price - np.random.rand(100) * 2
    
    sample_df = pd.DataFrame({
        'close_price': price,
        'high_price': high,
        'low_price': low,
        'sma_20': pd.Series(price).rolling(20).mean()
    }, index=dates)
    
    # Calculate ATR manually for testing
    hl = sample_df['high_price'] - sample_df['low_price']
    hc = abs(sample_df['high_price'] - sample_df['close_price'].shift(1))
    lc = abs(sample_df['low_price'] - sample_df['close_price'].shift(1))
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    sample_df['atr_14'] = tr.rolling(14).mean()
    
    strategy = VolatilityBreakout(sma_window=20, atr_window=14, atr_multiplier=1.5)
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nSignals generated:")
    signals = result_df[result_df['signal'].isin(['BUY', 'SELL'])]
    if not signals.empty:
        print(signals[['close_price', 'sma_20', 'atr_14', 'upper_threshold', 'lower_threshold', 'signal']].head(10))
    
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
