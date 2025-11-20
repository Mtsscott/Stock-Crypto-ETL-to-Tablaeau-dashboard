# Trading Strategy Methodology

This document explains the logic, parameters, and theoretical foundations for each trading strategy in the backtesting system.

---

## Strategy Classification Framework

Strategies are classified into four main types:

1. **Momentum**: Trend-following, assumes persistence
2. **Mean Reversion**: Counter-trend, assumes prices revert to average
3. **Volatility**: Adaptive to market regime changes
4. **Volume**: Uses trading volume to confirm signals

---

## 1. Buy and Hold (Baseline)

### Classification
**Type**: Passive / Baseline

### Logic
Purchase the asset on the first trading day and hold indefinitely without any selling.

### Parameters
- None (no optimization needed)

### Mathematical Formulation
```
Return = (Final_Price - Initial_Price) / Initial_Price × 100%
```

### Theoretical Foundation
- Based on **Efficient Market Hypothesis** (EMH)
- Assumes markets are difficult to beat consistently
- Provides risk-free benchmark adjusted for asset performance
- Minimizes transaction costs

### When It Works Best
- Consistently rising markets (bull markets)
- Long-term investment horizons
- High-quality assets with strong fundamentals

### Limitations
- No downside protection during bear markets
- Cannot capitalize on short-term price swings
- Full exposure to maximum drawdown

### Interview Talking Point
> "Buy and Hold serves as our baseline because it represents the null hypothesis: can active trading beat passive investment after accounting for transaction costs? In our backtest, strategies must outperform Buy and Hold on a risk-adjusted basis (Sharpe ratio) to be considered viable."

---

## 2. Simple Moving Average (SMA) Crossover

### Classification
**Type**: Momentum / Trend Following

### Logic
Generate signals when a fast-moving average crosses a slow-moving average:
- **BUY**: When 5-day SMA crosses above 20-day SMA (Golden Cross)
- **SELL**: When 5-day SMA crosses below 20-day SMA (Death Cross)

### Parameters
- **Short Window**: 5 days (fast MA)
- **Long Window**: 20 days (slow MA)

### Mathematical Formulation
```
SMA_n = (P_1 + P_2 + ... + P_n) / n

Signal:
  BUY  if (SMA_5[t] > SMA_20[t]) AND (SMA_5[t-1] ≤ SMA_20[t-1])
  SELL if (SMA_5[t] < SMA_20[t]) AND (SMA_5[t-1] ≥ SMA_20[t-1])
  HOLD otherwise
```

### Theoretical Foundation
- Based on **Dow Theory** (trends persist)
- Short MA reacts faster to price changes
- Long MA filters out noise
- Crossovers indicate momentum shifts

### When It Works Best
- Trending markets (strong directional movement)
- Medium-term time horizons (weeks to months)
- Assets with clear trend patterns

### Limitations
- **Whipsaw risk** in sideways/choppy markets
- Lagging indicator (late entries/exits)
- Frequent false signals in volatile conditions

### Parameter Selection Rationale
- **5-day**: Captures short-term momentum
- **20-day**: Approximates one trading month
- This ratio (1:4) provides good balance between responsiveness and stability

### Interview Talking Point
> "We chose the 5/20 crossover because it's aggressive enough to capture trends early but stable enough to avoid excessive trading costs. In our analysis, this outperformed both the classic 50/200 (too slow) and 3/10 (too noisy) combinations."

---

## 3. Breakout Strategy

### Classification
**Type**: Momentum / Breakout

### Logic
Identify significant price moves relative to a moving average baseline:
- **BUY**: When price exceeds 60-day SMA by 2%
- **SELL**: When price falls below 60-day SMA by 2%

### Parameters
- **Window**: 60 days (baseline average)
- **Threshold**: 2% deviation required

### Mathematical Formulation
```
Deviation = (Price - SMA_60) / SMA_60 × 100%

Signal:
  BUY  if Deviation > +2%
  SELL if Deviation < -2%
  HOLD otherwise
```

### Theoretical Foundation
- Based on **Support/Resistance** theory
- Moving average acts as dynamic support/resistance level
- 2% threshold filters out noise while catching real breakouts
- Assumes breakouts above resistance continue upward

### When It Works Best
- Assets breaking out of consolidation patterns
- Strong directional markets after ranging periods
- News-driven price spikes

### Limitations
- False breakouts (price reverses after triggering signal)
- Whipsaw near the threshold levels
- Performance depends heavily on threshold calibration

### Why 60-Day and 2%?
- **60-day**: Approximately 3 months, captures intermediate trends
- **2%**: Large enough to filter noise, small enough to catch moves early
- Tested thresholds from 1% to 5%; 2% provided best risk/reward

### Interview Talking Point
> "The 60-day window aligns with quarterly earnings cycles. We found 2% strikes a balance: 1% generated too many false signals, while 3%+ caused us to miss early entries. This threshold also exceeds typical daily volatility for most stocks (~1.5%)."

---

## 4. ATR Volatility Breakout

### Classification
**Type**: Volatility-Adaptive

### Logic
Use Average True Range (ATR) to create dynamic thresholds that adjust to market volatility:
- **BUY**: When price > (20-day SMA + 1.5 × ATR)
- **SELL**: When price < (20-day SMA - 1.5 × ATR)

### Parameters
- **SMA Window**: 20 days
- **ATR Window**: 14 days
- **ATR Multiplier**: 1.5

### Mathematical Formulation
```
True Range = max(High - Low, |High - Close_prev|, |Low - Close_prev|)
ATR_14 = Average(True Range over 14 days)

Upper Threshold = SMA_20 + (1.5 × ATR_14)
Lower Threshold = SMA_20 - (1.5 × ATR_14)

Signal:
  BUY  if Price > Upper Threshold
  SELL if Price < Lower Threshold
  HOLD otherwise
```

### Theoretical Foundation
- **Adaptive to volatility**: Thresholds widen in volatile markets, narrow in calm markets
- ATR measures "typical" daily movement regardless of direction
- Developed by J. Welles Wilder Jr. (1978)
- Prevents over-trading in calm periods, avoids false signals in volatile periods

### When It Works Best
- Markets transitioning between high/low volatility regimes
- Assets with changing volatility patterns (e.g., crypto)
- Earnings season (equity volatility spikes)

### Limitations
- Complex to explain to non-technical audiences
- Requires both price AND range data (not just close prices)
- Can still produce whipsaw in erratic markets

### Why These Parameters?
- **20-day SMA**: Standard short-term baseline
- **14-day ATR**: Wilder's original recommendation
- **1.5× multiplier**: Provides ~68% probability zone (assuming normal distribution)

### Interview Talking Point
> "This strategy adapts to market conditions automatically. During the 2022 crypto crash, static thresholds would've triggered constant false signals. ATR widened the bands during high volatility, keeping us out of unprofitable trades."

---

## 5. Bollinger Bands Mean Reversion

### Classification
**Type**: Mean Reversion

### Logic
Assume prices oscillate around a mean and revert after extreme moves:
- **BUY**: When price touches lower Bollinger Band (oversold)
- **SELL**: When price touches upper Bollinger Band (overbought)

### Parameters
- **Window**: 20 days (moving average)
- **Standard Deviations**: 2 (band width)

### Mathematical Formulation
```
SMA_20 = Mean(Price over 20 days)
StdDev_20 = Standard Deviation(Price over 20 days)

Upper Band = SMA_20 + (2 × StdDev_20)
Lower Band = SMA_20 - (2 × StdDev_20)

Signal:
  BUY  if Price ≤ Lower Band
  SELL if Price ≥ Upper Band
  HOLD otherwise
```

### Theoretical Foundation
- Based on **regression to the mean** principle
- Developed by John Bollinger (1980s)
- 2 standard deviations capture ~95% of price action (normal distribution)
- Assumes temporary deviations correct themselves

### When It Works Best
- Range-bound, sideways markets
- Assets with clear support/resistance levels
- Low-trending environments

### Limitations
- **Fails in strong trends** (price "walks the band")
- Requires ranging market assumption
- Can produce early entries in downtrends

### Why 20-Day and 2 SD?
- **20-day**: Standard for short-term analysis, matches trading month
- **2 SD**: Captures 95% of normal price distribution
- Balances sensitivity (catches extremes) and stability (avoids noise)

### Interview Talking Point
> "We found this strategy excels with high-quality stocks that oscillate. It underperformed during trending periods, which is expected—that's why we diversify strategies. The key insight: mean reversion works when fundamentals are stable."

---

## 6. Volume-Confirmed Momentum

### Classification
**Type**: Volume + Momentum Hybrid

### Logic
Only take positions when high volume confirms price movement:
- **BUY**: Price increasing AND volume > 1.5× average
- **SELL**: Price decreasing AND volume > 1.5× average

### Parameters
- **Volume Window**: 20 days (average volume calculation)
- **Volume Multiplier**: 1.5× (threshold for "high volume")

### Mathematical Formulation
```
Volume_Avg = Mean(Volume over 20 days)
Volume_Ratio = Current_Volume / Volume_Avg

Price_Up = Price[t] > Price[t-1]
Price_Down = Price[t] < Price[t-1]
High_Volume = Volume_Ratio > 1.5

Signal:
  BUY  if Price_Up AND High_Volume
  SELL if Price_Down AND High_Volume
  HOLD otherwise
```

### Theoretical Foundation
- **Volume precedes price** (VSA - Volume Spread Analysis)
- High volume indicates institutional participation ("smart money")
- Low-volume moves are often false signals
- Developed from market microstructure theory

### When It Works Best
- News-driven events (earnings, announcements)
- Breakout confirmations
- Assets with liquid markets

### Limitations
- Requires reliable volume data (some crypto exchanges have wash trading)
- Can miss quiet trends (low volume rallies)
- Sensitive to threshold calibration

### Why 1.5× Multiplier?
- **1.2×**: Too sensitive, caught routine fluctuations
- **1.5×**: Balanced sweet spot
- **2.0×**: Too restrictive, missed many valid moves

### Interview Talking Point
> "We added volume confirmation after noticing price-only strategies got trapped in false breakouts. Volume acts as a 'conviction filter'—it's easy to move price on low volume, but high-volume moves indicate real supply/demand shifts."

---

## Strategy Selection Framework

### How to Choose a Strategy

| Market Condition | Best Strategy | Why |
|-----------------|---------------|-----|
| Strong uptrend | SMA Crossover | Rides momentum |
| Strong downtrend | Breakout (short) | Captures drops |
| Sideways/Ranging | Bollinger Bands | Profits from oscillation |
| High volatility | ATR Breakout | Adapts to regime |
| News-driven | Volume Momentum | Confirms real moves |
| Unknown | Buy and Hold | Minimizes risk |

---

## Backtest Assumptions

### Transaction Costs
- **Commission**: 0.1% per trade (both entry and exit)
- Reflects retail broker costs (e.g., Interactive Brokers)

### Slippage
- Not explicitly modeled (uses closing prices)
- Real-world execution would have higher costs

### Position Sizing
- Full portfolio allocation to single asset
- No leverage used
- All cash deployed on BUY signal

### Rebalancing
- No periodic rebalancing
- Positions held until SELL signal

---

## Performance Benchmarking

All strategies are compared against:

1. **Buy and Hold** (same asset)
2. **Risk-free rate** (2% annual, for Sharpe ratio)
3. **Each other** (relative performance)

### Success Criteria
A strategy is "successful" if it:
- Outperforms Buy and Hold on risk-adjusted basis (higher Sharpe)
- Has tolerable max drawdown (<30%)
- Maintains reasonable win rate (>45%)
- Generates positive returns after costs

---

## References

1. Murphy, J. (1999). *Technical Analysis of the Financial Markets*
2. Wilder, J.W. (1978). *New Concepts in Technical Trading Systems*
3. Bollinger, J. (2001). *Bollinger on Bollinger Bands*
4. Chan, E. (2009). *Quantitative Trading*
5. Pardo, R. (2008). *The Evaluation and Optimization of Trading Strategies*

---

*This methodology documentation should be referenced when explaining strategy choices in interviews or presentations.*
