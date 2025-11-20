"""
Base class for all trading strategies.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    All strategies must implement the generate_signals() method.
    """
    
    def __init__(self, name: str, strategy_type: str, parameters: Dict[str, Any]):
        """
        Initialize strategy.
        
        Args:
            name: Strategy display name
            strategy_type: Type category (Momentum, Mean Reversion, etc.)
            parameters: Dictionary of strategy parameters
        """
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = parameters
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy logic.
        
        Args:
            df: DataFrame with OHLCV data and technical indicators
                Must have index as DatetimeIndex
                
        Returns:
            DataFrame with added 'signal' column containing:
                'BUY'  - Enter long position
                'SELL' - Exit position / Go flat
                'HOLD' - Maintain current position
        
        Note: The first valid signal should be either BUY or HOLD.
              Strategies should not alternate BUY-SELL-BUY without HOLD.
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame has required columns for the strategy.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        required = self.get_required_columns()
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            print(f"  ✗ Missing required columns: {missing}")
            return False
        
        return True
    
    @abstractmethod
    def get_required_columns(self) -> list:
        """
        Return list of required DataFrame columns for this strategy.
        
        Returns:
            List of column names
        """
        pass
    
    def get_description(self) -> str:
        """
        Get human-readable strategy description.
        
        Returns:
            Strategy description string
        """
        return f"{self.name} ({self.strategy_type})"
    
    def get_parameters_str(self) -> str:
        """
        Get formatted parameter string.
        
        Returns:
            String representation of parameters
        """
        return ", ".join([f"{k}={v}" for k, v in self.parameters.items()])
    
    def __repr__(self) -> str:
        """String representation of strategy."""
        return f"{self.__class__.__name__}({self.get_parameters_str()})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.get_description()


class SignalValidator:
    """Helper class to validate trading signals."""
    
    @staticmethod
    def validate_signals(df: pd.DataFrame) -> bool:
        """
        Validate signal column in DataFrame.
        
        Args:
            df: DataFrame with 'signal' column
            
        Returns:
            True if signals are valid
        """
        if 'signal' not in df.columns:
            print("  ✗ No 'signal' column found")
            return False
        
        valid_signals = {'BUY', 'SELL', 'HOLD'}
        invalid = set(df['signal'].unique()) - valid_signals
        
        if invalid:
            print(f"  ✗ Invalid signals found: {invalid}")
            return False
        
        # Check if there are any signals
        if df['signal'].isna().all():
            print("  ✗ All signals are NaN")
            return False
        
        return True
    
    @staticmethod
    def get_signal_summary(df: pd.DataFrame) -> Dict[str, int]:
        """
        Get summary of signals generated.
        
        Args:
            df: DataFrame with 'signal' column
            
        Returns:
            Dictionary with signal counts
        """
        return {
            'BUY': (df['signal'] == 'BUY').sum(),
            'SELL': (df['signal'] == 'SELL').sum(),
            'HOLD': (df['signal'] == 'HOLD').sum(),
            'Total': len(df)
        }
