"""
Trading strategy implementations.

All strategies inherit from BaseStrategy and implement the generate_signals() method.
"""
from .base_strategy import BaseStrategy, SignalValidator
from .buy_and_hold import BuyAndHold
from .sma_crossover import SMACrossover
from .breakout_strategy import BreakoutStrategy
from .volatility_strategy import VolatilityBreakout
from .mean_reversion import BollingerMeanReversion
from .volume_momentum import VolumeMomentum

__all__ = [
    'BaseStrategy',
    'SignalValidator',
    'BuyAndHold',
    'SMACrossover',
    'BreakoutStrategy',
    'VolatilityBreakout',
    'BollingerMeanReversion',
    'VolumeMomentum'
]
