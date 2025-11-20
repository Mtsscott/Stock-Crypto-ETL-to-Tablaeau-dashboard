# System Architecture

This document describes the technical architecture, data flow, and design decisions for the Stock & Crypto Trading Strategy Backtesting System.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Tableau Desktop │  │ Jupyter Notebooks│                │
│  │   Dashboards     │  │   Analysis       │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────────────┬──────────────────┬─────────────────────┘
                     │                  │
                     ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐         │
│  │ Backtesting│  │  Feature   │  │ Data Ingestion│         │
│  │   Engine   │  │  Pipeline  │  │    Pipeline   │         │
│  └────────────┘  └────────────┘  └───────────────┘         │
│  ┌────────────────────────────────────────────────┐         │
│  │         Strategy Implementations (6)           │         │
│  └────────────────────────────────────────────────┘         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌──────────────────────────────────────────────┐           │
│  │         SQL Server Database (Star Schema)    │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │           │
│  │  │   Dim    │  │   Dim    │  │   Dim    │   │           │
│  │  │  Tables  │  │  Tables  │  │  Tables  │   │           │
│  │  └──────────┘  └──────────┘  └──────────┘   │           │
│  │  ┌────────────────────────────────────────┐ │           │
│  │  │         Fact Tables (5)                │ │           │
│  │  └────────────────────────────────────────┘ │           │
│  └──────────────────────────────────────────────┘           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL DATA SOURCE                       │
│               Alpha Vantage REST API                         │
│      (Stock & Crypto OHLCV + Volume Data)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Data Ingestion Pipeline

**Responsibility**: Fetch raw price data from external API and load into database.

**Components**:
- `api_client.py`: HTTP client for Alpha Vantage API
- `data_loader.py`: Database insertion logic
- `fetch_latest_data.py`: Orchestration script

**Data Flow**:
```
Alpha Vantage API
    ↓ (HTTP GET)
Raw JSON Response
    ↓ (Parse & Transform)
Pandas DataFrame
    ↓ (Validate & Clean)
SQL Server (fact_prices)
```

**Key Design Decisions**:
- **Rate Limiting**: 15-second delay between API calls (Alpha Vantage limit: 5 calls/min)
- **Incremental Loading**: Only insert new records (avoids duplicates)
- **Error Handling**: Continues processing other tickers if one fails
- **Idempotency**: Safe to run multiple times without corruption

**Performance**: ~5 minutes for 20 tickers (limited by API rate)

---

### 2. Feature Engineering Pipeline

**Responsibility**: Calculate technical indicators from price data.

**Components**:
- `indicators.py`: Pure functions for each indicator
- `feature_pipeline.py`: Orchestration and database persistence
- `calculate_indicators.py`: Executable script

**Indicators Calculated** (15 total):
- Moving Averages: SMA(5, 10, 20, 60, 90, 200)
- Volatility: ATR(14), StdDev(20), Bollinger Bands
- Volume: Volume SMA(20), Volume Ratio
- Price Metrics: Price vs SMA %, Distance from Mean

**Data Flow**:
```
fact_prices (raw OHLCV)
    ↓ (Join with dim_date, dim_ticker)
Pandas DataFrame (loaded to memory)
    ↓ (Apply indicator functions)
DataFrame with 15+ new columns
    ↓ (Save to database)
fact_technical_indicators
```

**Optimization Techniques**:
- **Vectorized Operations**: Pandas rolling windows (fast)
- **Batch Processing**: Calculate all indicators in single pass
- **Database Views**: Pre-joined data for faster loading

**Performance**: ~30 seconds for all tickers (50k+ records)

---

### 3. Trading Strategies

**Responsibility**: Implement signal generation logic.

**Design Pattern**: Template Method (Abstract Base Class)

```python
BaseStrategy (Abstract)
    │
    ├── generate_signals() [ABSTRACT]
    ├── validate_data()
    ├── get_required_columns() [ABSTRACT]
    └── get_description()

Concrete Implementations:
    ├── BuyAndHold
    ├── SMACrossover
    ├── BreakoutStrategy
    ├── VolatilityBreakout
    ├── BollingerMeanReversion
    └── VolumeMomentum
```

**Key Principles**:
- **Single Responsibility**: Each strategy = one signal generation approach
- **Dependency Injection**: Strategies receive data, don't query database
- **Testability**: Can unit test with synthetic data
- **Extensibility**: Add new strategy by creating subclass

**Signal Types**:
- `BUY`: Enter long position
- `SELL`: Exit position
- `HOLD`: Maintain current state (or stay flat)

---

### 4. Backtesting Engine

**Responsibility**: Simulate trading based on historical data and signals.

**Components**:
- `portfolio.py`: Tracks cash, positions, trades
- `backtest_engine.py`: Main simulation loop
- `performance_metrics.py`: Calculate results

**Simulation Loop**:
```python
for each day in historical_data:
    signal = strategy.generate_signal(day)
    
    if signal == 'BUY' and not holding_position:
        portfolio.buy(price, date)
    
    elif signal == 'SELL' and holding_position:
        portfolio.sell(price, date)
    
    portfolio.record_daily_state(price, date)

# After loop ends
calculate_performance_metrics(portfolio)
save_results_to_database()
```

**Realism Features**:
- **Transaction Costs**: 0.1% commission per trade
- **No Lookahead Bias**: Uses only data available at each point in time
- **Position Tracking**: Enforces one position at a time (no pyramiding)
- **Slippage**: Uses closing prices (simplification, but consistent)

**What's NOT Modeled** (limitations):
- Market impact (assumes small orders)
- Bid-ask spread
- Dividend payments
- Stock splits
- Margin trading / leverage

---

### 5. Database Schema

**Design**: Kimball Star Schema (optimized for analytics)

#### Dimension Tables

**dim_ticker**
```sql
ticker_id (PK)
ticker_symbol (UNIQUE)
company_name
asset_type (Stock/Crypto)
```

**dim_date**
```sql
date_id (PK)
trade_date (UNIQUE)
year, month, day
day_of_week
quarter
```

**dim_strategy**
```sql
strategy_id (PK)
strategy_name (UNIQUE)
strategy_type
strategy_description
parameters (JSON)
```

#### Fact Tables

**fact_prices** (Raw Market Data)
```sql
price_id (PK)
ticker_id (FK) ─┐
date_id (FK) ───┼─ UNIQUE constraint
open_price      │
high_price      │
low_price       │
close_price     │
volume          │
pct_change     ─┘
```

**fact_technical_indicators** (Calculated Metrics)
```sql
indicator_id (PK)
ticker_id (FK) ─┐
date_id (FK) ───┼─ UNIQUE constraint
sma_5, sma_10, sma_20, sma_60, sma_90, sma_200
atr_14, std_dev_20
bollinger_upper, bollinger_middle, bollinger_lower
volume_sma_20, volume_ratio
price_vs_sma60_pct, distance_from_mean
```

**fact_trades** (Individual Trade Records)
```sql
trade_id (PK)
ticker_id (FK)
strategy_id (FK)
entry_date_id (FK), exit_date_id (FK)
entry_price, exit_price
shares
trade_return_pct, trade_return_dollars
holding_days
trade_status (WIN/LOSS/OPEN)
```

**fact_strategy_performance** (Daily Portfolio Snapshots)
```sql
performance_id (PK)
ticker_id (FK) ───┐
strategy_id (FK) ─┼─ UNIQUE(ticker, strategy, date)
date_id (FK) ─────┘
portfolio_value
cash_balance, position_value, shares_held
cumulative_return_pct
total_trades, winning_trades, losing_trades
```

**fact_strategy_summary** (Aggregated Results)
```sql
summary_id (PK)
ticker_id (FK) ──┐
strategy_id (FK) ┴─ UNIQUE(ticker, strategy)
start_date, end_date
final_portfolio_value
total_return_pct, annualized_return_pct
sharpe_ratio, max_drawdown_pct, volatility
total_trades, winning_trades, losing_trades
win_rate_pct, avg_win_pct, avg_loss_pct
profit_factor, avg_holding_days
calculated_at
```

**Why Star Schema?**:
- **Fast Aggregations**: Tableau queries are efficient
- **Simple Joins**: Dimension → Fact (no complex navigation)
- **Scalable**: Easy to add new tickers/strategies
- **Understandable**: Business users can grasp relationships

**Normalization Level**: 3NF for dimensions, denormalized facts

---

## Data Flow Diagrams

### Daily Update Flow

```
                 Daily Scheduled Job
                        │
                        ▼
         ┌──────────────────────────────┐
         │  1. fetch_latest_data.py     │
         │     (New price records)      │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  2. calculate_indicators.py  │
         │     (Update indicators)      │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  3. run_backtests.py         │
         │     (Recalculate metrics)    │
         └──────────────┬───────────────┘
                        │
                        ▼
                Tableau Auto-Refresh
```

### Backtest Execution Flow

```
run_backtests.py
    │
    ├─ For each ticker:
    │     │
    │     ├─ For each strategy:
    │     │     │
    │     │     ├─ Load data (prices + indicators)
    │     │     │     ↓
    │     │     ├─ strategy.generate_signals()
    │     │     │     ↓
    │     │     ├─ backtest_engine.run()
    │     │     │     │
    │     │     │     ├─ Simulate trades
    │     │     │     ├─ Track portfolio
    │     │     │     └─ Calculate metrics
    │     │     │           ↓
    │     │     └─ save_results_to_database()
    │     │           ├─ fact_trades
    │     │           ├─ fact_strategy_performance
    │     │           └─ fact_strategy_summary
    │     │
    │     └─ Next strategy
    │
    └─ Summary report (console output)
```

---

## Technology Choices

### Why Python?
- **Pros**: Rich data science ecosystem (pandas, numpy)
- **Cons**: Slower than compiled languages
- **Justification**: Productivity > raw speed for this use case

### Why SQL Server?
- **Pros**: Excellent Tableau integration, familiar to employers
- **Cons**: Windows-only (without Docker), license costs
- **Alternatives**: PostgreSQL (free, cross-platform)

### Why Pandas?
- **Pros**: DataFrame API perfect for time-series
- **Cons**: Memory-intensive for very large datasets
- **Optimization**: Process tickers individually (avoid loading all data)

### Why Not Spark/Big Data?
- **Scale**: 50k records ≠ "big data"
- **Complexity**: Overkill for this dataset
- **Portfolio Focus**: Demonstrate fundamentals, not buzzwords

---

## Scalability Considerations

### Current Limitations

| Aspect | Current | Bottleneck |
|--------|---------|------------|
| Tickers | 20 | API rate limit |
| History | 5+ years | Database size OK |
| Strategies | 6 | None (can add many) |
| Indicators | 15 | Calculation time grows linearly |
| Backtest Speed | 1 sec/ticker | Single-threaded |

### How to Scale (Future)

**10× More Tickers (200)**:
- Parallelize API calls with ThreadPoolExecutor
- Use multiple API keys (if available)
- Switch to WebSocket feeds for real-time data

**100× More Data (5M records)**:
- Partition tables by date or ticker
- Use columnar storage (Parquet files)
- Consider time-series database (InfluxDB, TimescaleDB)

**Real-Time Processing**:
- Replace batch jobs with stream processing (Kafka + Flink)
- Use Redis for caching latest indicators
- WebSocket API for live signals

---

## Security & Best Practices

### Implemented

✅ **Environment Variables**: API keys in `.env` (not committed to Git)
✅ **SQL Injection Prevention**: SQLAlchemy parameterized queries
✅ **Error Handling**: Try-except blocks with logging
✅ **Type Hints**: Function signatures include types
✅ **Docstrings**: All public functions documented

### Not Implemented (Production Would Need)

❌ **Authentication**: Database uses trusted connection
❌ **Encryption**: Data in transit (HTTPS) but not at rest
❌ **Audit Logging**: No trail of who changed what
❌ **Backup Strategy**: Manual backups only
❌ **CI/CD Pipeline**: No automated testing on commit

---

## Testing Strategy

### Unit Tests
- `tests/test_indicators.py`: Verify math correctness
- `tests/test_strategies.py`: Signal generation logic
- `tests/test_portfolio.py`: Trade execution mechanics

### Integration Tests
- End-to-end pipeline test with sample data
- Database connection validation

### Manual Tests
- Visual inspection of Tableau dashboards
- Sanity checks (returns are reasonable, no negative prices)

**Coverage Goal**: 80%+ for core logic (strategies, indicators)

---

## Deployment

### Development Environment
```
Local Machine
├── Python 3.8+ (Anaconda)
├── SQL Server Express (LocalDB)
├── Tableau Desktop (14-day trial or student license)
└── VS Code / PyCharm
```

### "Production" (Portfolio Showcase)
```
Cloud VM (Optional)
├── SQL Server (Azure SQL or AWS RDS)
├── Python scripts as scheduled jobs
├── Tableau Public (free hosting)
└── GitHub Pages (documentation)
```

---

## Performance Benchmarks

**Measured on**: Intel i7, 16GB RAM, SSD

| Task | Time | Records |
|------|------|---------|
| Fetch 1 ticker data | 3 sec | ~2,500 |
| Calculate indicators (all) | 30 sec | 50,000 |
| Run 1 backtest | 0.5 sec | 2,500 |
| Full pipeline (20 tickers, 6 strategies) | 8 min | 120 backtests |
| Tableau dashboard load | 2 sec | Pre-aggregated view |

---

## Maintenance & Monitoring

### Daily Checks
- ✅ API call success rate
- ✅ New records inserted count
- ✅ Backtest completion status

### Weekly Reviews
- 📊 Performance drift (strategies degrade over time?)
- 📈 Data quality (missing dates, outliers)

### Monthly Tasks
- 🔄 Database vacuuming / index rebuild
- 📦 Export data backups
- 🆕 Evaluate new strategies to add

---

## References & Inspirations

**Architecture Patterns**:
- *Designing Data-Intensive Applications* by Martin Kleppmann
- *The Data Warehouse Toolkit* by Ralph Kimball

**Algorithmic Trading**:
- *Quantitative Trading* by Ernest Chan
- *Advances in Financial Machine Learning* by Marcos López de Prado

**Similar Projects**:
- [Zipline](https://github.com/quantopian/zipline) - Pythonic backtesting library
- [Backtrader](https://www.backtrader.com/) - Feature-rich backtesting framework
- [QuantConnect](https://www.quantconnect.com/) - Cloud algo trading platform

---

## Evolution History

**v1.0** (Current)
- Basic ETL pipeline
- 6 trading strategies
- SQL Server warehouse
- Tableau dashboards

**Future v2.0** (Roadmap)
- Machine learning strategies
- Real-time data feeds
- Web dashboard (Flask/Dash)
- Portfolio optimization

---

*This architecture document should be used alongside code comments and other documentation for complete understanding of the system.*
