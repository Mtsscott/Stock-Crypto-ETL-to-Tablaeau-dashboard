"""
Volume-Confirmed Momentum Strategy.

Buy when high volume confirms upward price movement.
Sell when high volume confirms downward price movement.
"""
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy


class VolumeMomentum(BaseStrategy):
    """
    Volume-Confirmed Momentum Strategy.
    
    Only takes positions when volume confirms the price movement,
    indicating strong market conviction. Requires above-average volume
    to validate momentum signals.
    """
    
    def __init__(self, volume_window: int = 20, volume_multiplier: float = 1.5):
        """
        Initialize Volume Momentum Strategy.
        
        Args:
            volume_window: Window for average volume calculation (default 20)
            volume_multiplier: Minimum volume multiple to confirm signal (default 1.5x)
        """
        parameters = {
            "volume_window": volume_window,
            "volume_multiplier": volume_multiplier
        }
        
        super().__init__(
            name="Volume Momentum",
            strategy_type="Volume",
            parameters=parameters
        )
        
        self.volume_window = volume_window
        self.volume_multiplier = volume_multiplier
    
    def get_required_columns(self) -> list:
        """Return required columns for this strategy."""
        return [
            'close_price',
            'volume',
            f'volume_sma_{self.volume_window}',
            'volume_ratio'
        ]
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on volume-confirmed momentum.
        
        Args:
            df: DataFrame with price and volume data
            
        Returns:
            DataFrame with 'signal' column added
        """
        if not self.validate_data(df):
            raise ValueError(f"DataFrame missing required columns for {self.name}")
        
        df = df.copy()
        
        # Calculate price momentum (simple direction)
        df['price_change'] = df['close_price'].diff()
        df['price_up'] = df['price_change'] > 0
        df['price_down'] = df['price_change'] < 0
        
        # High volume condition
        df['high_volume'] = df['volume_ratio'] >= self.volume_multiplier
        
        # Initialize signal column
        df['signal'] = 'HOLD'
        
        # BUY: Price increasing + high volume
        buy_condition = df['price_up'] & df['high_volume']
        df.loc[buy_condition, 'signal'] = 'BUY'
        
        # SELL: Price decreasing + high volume
        sell_condition = df['price_down'] & df['high_volume']
        df.loc[sell_condition, 'signal'] = 'SELL'
        
        # Additional confirmation: look for consecutive signals
        # This helps avoid whipsaw trades from single-day spikes
        df['consecutive_up'] = (
            df['price_up'] & 
            df['price_up'].shift(1) & 
            df['high_volume']
        )
        df['consecutive_down'] = (
            df['price_down'] & 
            df['price_down'].shift(1) & 
            df['high_volume']
        )
        
        # Override with consecutive signals (stronger confirmation)
        df.loc[df['consecutive_up'], 'signal'] = 'BUY'
        df.loc[df['consecutive_down'], 'signal'] = 'SELL'
        
        # Initial position: wait for first clear signal
        first_valid_idx = df[['close_price', 'volume_ratio']].first_valid_index()
        if first_valid_idx is not None:
            # Start with no position
            df.loc[first_valid_idx, 'signal'] = 'HOLD'
        
        return df
    
    def get_description(self) -> str:
        """Get strategy description."""
        return (
            f"{self.name}: Buy when price increases on volume > "
            f"{self.volume_multiplier}x average ({self.volume_window}-day), "
            f"sell when price decreases on high volume."
        )


if __name__ == "__main__":
    # Test the strategy
    print("Testing Volume Momentum Strategy...")
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulate price with occasional high-volume moves
    price = 100 + np.random.randn(100).cumsum()
    volume = np.random.randint(1000000, 3000000, 100)
    
    # Add some high-volume spikes
    high_vol_days = [20, 21, 50, 51, 80, 81]
    volume[high_vol_days] = np.random.randint(5000000, 8000000, len(high_vol_days))
    
    sample_df = pd.DataFrame({
        'close_price': price,
        'volume': volume
    }, index=dates)
    
    # Calculate volume indicators
    window = 20
    sample_df['volume_sma_20'] = sample_df['volume'].rolling(window).mean()
    sample_df['volume_ratio'] = sample_df['volume'] / sample_df['volume_sma_20']
    
    strategy = VolumeMomentum(volume_window=20, volume_multiplier=1.5)
    result_df = strategy.generate_signals(sample_df)
    
    print(f"\nStrategy: {strategy.get_description()}")
    print(f"\nSignals generated:")
    signals = result_df[result_df['signal'].isin(['BUY', 'SELL'])]
    if not signals.empty:
        print(signals[['close_price', 'volume', 'volume_ratio', 'price_change', 'signal']].head(15))
    else:
        print("No signals generated")
    
    from .base_strategy import SignalValidator
    summary = SignalValidator.get_signal_summary(result_df)
    print(f"\nSignal Summary: {summary}")
