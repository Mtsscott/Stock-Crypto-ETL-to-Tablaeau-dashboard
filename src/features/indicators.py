"""
Technical indicator calculations for trading strategies.
"""
import pandas as pd
import numpy as np


def calculate_sma(df: pd.DataFrame, column: str = 'close_price', windows: list = None) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages for multiple windows.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate SMA on
        windows: List of window sizes (default: [5, 10, 20, 60, 90, 200])
        
    Returns:
        DataFrame with added SMA columns
    """
    if windows is None:
        windows = [5, 10, 20, 60, 90, 200]
    
    df = df.copy()
    
    for window in windows:
        df[f'sma_{window}'] = df[column].rolling(window=window, min_periods=1).mean()
    
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR) - volatility indicator.
    
    Args:
        df: DataFrame with high, low, close prices
        period: Lookback period (default 14)
        
    Returns:
        DataFrame with added atr column
    """
    df = df.copy()
    
    # True Range is the max of:
    # 1. Current High - Current Low
    # 2. |Current High - Previous Close|
    # 3. |Current Low - Previous Close|
    
    high_low = df['high_price'] - df['low_price']
    high_close = abs(df['high_price'] - df['close_price'].shift(1))
    low_close = abs(df['low_price'] - df['close_price'].shift(1))
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # ATR is the moving average of True Range
    df[f'atr_{period}'] = true_range.rolling(window=period, min_periods=1).mean()
    
    return df


def calculate_bollinger_bands(
    df: pd.DataFrame, 
    column: str = 'close_price',
    window: int = 20, 
    num_std: float = 2.0
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate bands on
        window: Moving average window (default 20)
        num_std: Number of standard deviations (default 2)
        
    Returns:
        DataFrame with bollinger_upper, bollinger_middle, bollinger_lower
    """
    df = df.copy()
    
    # Middle band is SMA
    df['bollinger_middle'] = df[column].rolling(window=window, min_periods=1).mean()
    
    # Calculate rolling standard deviation
    rolling_std = df[column].rolling(window=window, min_periods=1).std()
    
    # Upper and lower bands
    df['bollinger_upper'] = df['bollinger_middle'] + (rolling_std * num_std)
    df['bollinger_lower'] = df['bollinger_middle'] - (rolling_std * num_std)
    
    return df


def calculate_std_dev(df: pd.DataFrame, column: str = 'close_price', window: int = 20) -> pd.DataFrame:
    """
    Calculate rolling standard deviation.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate std on
        window: Rolling window size
        
    Returns:
        DataFrame with std_dev column
    """
    df = df.copy()
    df[f'std_dev_{window}'] = df[column].rolling(window=window, min_periods=1).std()
    return df


def calculate_volume_indicators(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate volume-based indicators.
    
    Args:
        df: DataFrame with volume data
        window: Moving average window for volume
        
    Returns:
        DataFrame with volume_sma and volume_ratio
    """
    df = df.copy()
    
    # Average volume
    df[f'volume_sma_{window}'] = df['volume'].rolling(window=window, min_periods=1).mean()
    
    # Volume ratio (current volume / average volume)
    df['volume_ratio'] = df['volume'] / df[f'volume_sma_{window}']
    df['volume_ratio'] = df['volume_ratio'].replace([np.inf, -np.inf], np.nan)
    
    return df


def calculate_price_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate price-based metrics for strategies.
    
    Args:
        df: DataFrame with price and SMA data
        
    Returns:
        DataFrame with additional price metrics
    """
    df = df.copy()
    
    # Price vs 60-day SMA (percentage difference)
    if 'sma_60' in df.columns:
        df['price_vs_sma60_pct'] = (
            (df['close_price'] - df['sma_60']) / df['sma_60'] * 100
        )
    
    # Distance from 90-day mean in standard deviations
    if 'sma_90' in df.columns and 'std_dev_20' in df.columns:
        df['distance_from_mean'] = (
            (df['close_price'] - df['sma_90']) / df['std_dev_20']
        )
    
    return df


def calculate_rsi(df: pd.DataFrame, column: str = 'close_price', period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        df: DataFrame with price data
        column: Column to calculate RSI on
        period: Lookback period (default 14)
        
    Returns:
        DataFrame with rsi column
    """
    df = df.copy()
    
    # Calculate price changes
    delta = df[column].diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period, min_periods=1).mean()
    avg_losses = losses.rolling(window=period, min_periods=1).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    df[f'rsi_{period}'] = rsi
    
    return df


def calculate_macd(
    df: pd.DataFrame, 
    column: str = 'close_price',
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        df: DataFrame with price data
        column: Column to calculate MACD on
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        DataFrame with macd and macd_signal columns
    """
    df = df.copy()
    
    # Calculate EMAs
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    
    # MACD line
    df['macd'] = ema_fast - ema_slow
    
    # Signal line (EMA of MACD)
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    
    return df


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators needed for strategies.
    
    Args:
        df: DataFrame with OHLCV data (columns: open_price, high_price, 
            low_price, close_price, volume)
            
    Returns:
        DataFrame with all indicators added
    """
    # Make a copy to avoid modifying original
    df = df.copy()
    
    print(f"  Calculating indicators for {len(df)} records...")
    
    # Moving Averages
    df = calculate_sma(df, column='close_price', windows=[5, 10, 20, 60, 90, 200])
    
    # Volatility Indicators
    df = calculate_atr(df, period=14)
    df = calculate_std_dev(df, column='close_price', window=20)
    df = calculate_bollinger_bands(df, column='close_price', window=20, num_std=2.0)
    
    # Volume Indicators
    df = calculate_volume_indicators(df, window=20)
    
    # Price Metrics
    df = calculate_price_metrics(df)
    
    # Optional: RSI and MACD (for future strategies)
    df = calculate_rsi(df, column='close_price', period=14)
    df = calculate_macd(df, column='close_price')
    
    print(f" Calculated {len(df.columns) - 6} indicators")  # -6 for original OHLCV+ticker
    
    return df


def validate_indicators(df: pd.DataFrame) -> bool:
    """
    Validate that all required indicators were calculated.
    
    Args:
        df: DataFrame with indicators
        
    Returns:
        True if valid, False otherwise
    """
    required_columns = [
        'sma_5', 'sma_20', 'sma_60', 'sma_90',
        'atr_14', 'std_dev_20',
        'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
        'volume_sma_20', 'volume_ratio'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f" Missing indicators: {missing}")
        return False
    
    # Check for excessive NaN values
    nan_pct = df[required_columns].isna().sum() / len(df) * 100
    high_nan = nan_pct[nan_pct > 50]
    
    if not high_nan.empty:
        print(f" High NaN percentage in: {high_nan.to_dict()}")
        return False
    
    print(f"  ✓ All indicators validated")
    return True


if __name__ == "__main__":
    # Test with sample data
    print("Testing indicator calculations...")
    
    # Create sample price data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    sample_df = pd.DataFrame({
        'trade_date': dates,
        'open_price': 100 + np.random.randn(100).cumsum(),
        'high_price': 102 + np.random.randn(100).cumsum(),
        'low_price': 98 + np.random.randn(100).cumsum(),
        'close_price': 100 + np.random.randn(100).cumsum(),
        'volume': np.random.randint(1000000, 10000000, 100)
    }).set_index('trade_date')
    
    # Calculate indicators
    result_df = calculate_all_indicators(sample_df)
    
    print(f"\nOriginal columns: {list(sample_df.columns)}")
    print(f"With indicators: {list(result_df.columns)}")
    print(f"\nSample output:")
    print(result_df[['close_price', 'sma_20', 'bollinger_upper', 'bollinger_lower', 'atr_14']].tail())
    
    # Validate
    validate_indicators(result_df)
