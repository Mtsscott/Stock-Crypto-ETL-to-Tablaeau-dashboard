# Stock & Crypto Trading Strategy Backtesting System

A comprehensive data analytics and business intelligence project demonstrating end-to-end ETL, data warehousing, algorithmic trading strategy development, and performance visualization.

## 🎯 Project Overview

This system evaluates **6 trading strategies** across **20+ financial assets** (stocks and cryptocurrencies) using a star schema data warehouse, automated ETL pipelines, and rigorous backtesting methodology. Designed to showcase skills relevant to data analytics, business intelligence, and quantitative analysis roles.

### Key Features

 **Automated Data Ingestion**: ETL pipeline fetching daily OHLCV data from Alpha Vantage API
 **Star Schema Data Warehouse**: SQL Server database optimized for analytics
 **15+ Technical Indicators**: SMA, ATR, Bollinger Bands, RSI, MACD, volume metrics
 **6 Trading Strategies**: Momentum, mean reversion, volatility, and volume-based approaches
 **Backtesting Engine**: Realistic simulation with transaction costs and position tracking
 **Performance Analytics**: Sharpe ratio, max drawdown, win rate, profit factor
 **Tableau Dashboards**: Interactive visualizations for strategy comparison

## 🛠️ Tech Stack

- **Languages**: Python 3.8+, SQL (T-SQL)
- **Database**: Microsoft SQL Server
- **Libraries**: pandas, NumPy, SQLAlchemy, requests
- **Visualization**: Tableau Desktop/Public
- **APIs**: Alpha Vantage (Financial Data)

## 📁 Project Structure

```
stock-crypto-trading-system/
│
├── src/                          # Core application code
│   ├── database/                 # Database connection & schema management
│   ├── data_ingestion/           # API client & data loading
│   ├── features/                 # Technical indicator calculations
│   ├── strategies/               # Trading strategy implementations
│   └── backtesting/              # Backtesting engine & performance metrics
│
├── scripts/                      # Executable scripts
│   ├── fetch_latest_data.py      # Update price data
│   ├── calculate_indicators.py   # Compute technical indicators
│   └── run_backtests.py          # Execute all strategy backtests
│
├── notebooks/                    # Jupyter notebooks
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_strategy_testing.ipynb
│   └── 03_results_visualization.ipynb
│
├── sql/                          # SQL scripts
│   ├── create_schema.sql         # Database DDL
│   └── create_views.sql          # Views for Tableau
│
├── docs/                         # Documentation
│   ├── architecture.md           # System design
│   ├── strategy_methodology.md   # Strategy explanations
│   └── tableau_guide.md          # Dashboard documentation
│
├── requirements.txt              # Python dependencies
├── config.yaml                   # Configuration file
└── README.md                     # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- SQL Server 2016+ (or SQL Server Express)
- Alpha Vantage API key (free at https://www.alphavantage.co/support/#api-key)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/stock-crypto-trading-system.git
cd stock-crypto-trading-system
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Create .env file
echo "ALPHA_VANTAGE_API_KEY=your_key_here" > .env
echo "DB_SERVER=localhost" >> .env
echo "DB_NAME=StockCryptoDB" >> .env
```

4. **Setup database**
```bash
python -m src.database.schema
```

### Running the Pipeline

```bash
# Step 1: Fetch price data (takes ~5 minutes with API rate limits)
python scripts/fetch_latest_data.py

# Step 2: Calculate technical indicators
python scripts/calculate_indicators.py

# Step 3: Run backtests
python scripts/run_backtests.py

# View results in Tableau or via SQL queries
```

## 📈 Trading Strategies

### 1. **Buy and Hold** (Baseline)
- **Type**: Passive
- **Logic**: Buy on first day, hold indefinitely
- **Purpose**: Benchmark for active strategies

### 2. **SMA Crossover (5/20)**
- **Type**: Momentum
- **Logic**: Buy when 5-day SMA crosses above 20-day SMA
- **Best For**: Trending markets

### 3. **Breakout (60-day)**
- **Type**: Momentum
- **Logic**: Buy when price exceeds 60-day SMA by 2%
- **Best For**: Strong directional moves

### 4. **ATR Volatility Breakout**
- **Type**: Volatility
- **Logic**: Dynamic thresholds based on Average True Range
- **Best For**: Adapting to changing market conditions

### 5. **Bollinger Mean Reversion**
- **Type**: Mean Reversion
- **Logic**: Buy at lower band, sell at upper band
- **Best For**: Range-bound, oscillating markets

### 6. **Volume Momentum**
- **Type**: Volume-Confirmed
- **Logic**: Requires high volume to confirm price moves
- **Best For**: Filtering false breakouts

## 🏗️ Database Schema

**Star Schema Design** optimized for analytical queries:

### Dimension Tables
- `dim_ticker`: Asset metadata (20 tickers)
- `dim_date`: Calendar with date attributes
- `dim_strategy`: Strategy definitions and parameters

### Fact Tables
- `fact_prices`: Daily OHLCV data (~50,000 records)
- `fact_technical_indicators`: Calculated indicators
- `fact_trading_signals`: Daily buy/sell/hold signals
- `fact_trades`: Individual trade records
- `fact_strategy_performance`: Daily portfolio values
- `fact_strategy_summary`: Aggregated performance metrics

## 📊 Performance Metrics

The system calculates comprehensive performance metrics:

**Return Metrics**
- Total Return %
- Annualized Return %
- Compound Annual Growth Rate (CAGR)

**Risk Metrics**
- Sharpe Ratio (risk-adjusted return)
- Maximum Drawdown %
- Volatility (annualized standard deviation)

**Trading Metrics**
- Total Trades Executed
- Win Rate %
- Average Win/Loss %
- Profit Factor (gross profit / gross loss)
- Average Holding Period (days)

## 🎨 Tableau Dashboards

Interactive dashboards available in Tableau Public:

1. **Strategy Comparison Dashboard**
   - Side-by-side equity curves
   - Risk/return scatter plot
   - Performance leaderboard

2. **Individual Strategy Deep Dive**
   - Price chart with buy/sell signals
   - Trade distribution analysis
   - Rolling performance metrics

3. **Asset Analysis Dashboard**
   - Cross-asset correlation heatmap
   - Volatility comparison (stocks vs crypto)
   - Volume trend analysis

[View Dashboards](https://public.tableau.com/your-profile) *(link your Tableau Public)*

## 🧪 Testing

Run unit tests:
```bash
pytest tests/
```

Test individual components:
```bash
# Test database connection
python -m src.database.connection

# Test indicator calculations
python -m src.features.indicators

# Test a strategy
python -m src.strategies.sma_crossover
```

## 📝 Key Learnings & Design Decisions

### Why Star Schema?
- **Fast aggregations** for Tableau queries
- **Easy to understand** dimension/fact relationship
- **Scalable** to add new strategies or assets

### Why These Strategies?
- Cover major strategy families (momentum, reversion, volatility)
- Well-documented in finance literature
- Easy to explain in interviews
- Realistic for retail traders

### Handling API Rate Limits
- 15-second delay between calls (Alpha Vantage allows 5 calls/minute)
- Full data fetch takes ~5 minutes for 20 tickers
- Consider caching for development

## 🚧 Future Enhancements

- [ ] Add machine learning strategies (LSTM price prediction)
- [ ] Implement portfolio optimization (Markowitz)
- [ ] Real-time data streaming with WebSockets
- [ ] Options trading strategies
- [ ] Risk management with position sizing
- [ ] Paper trading integration

## 📚 Resources & References

- **Technical Analysis**: *Technical Analysis of Financial Markets* by John Murphy
- **Backtesting**: *Quantitative Trading* by Ernest Chan
- **Star Schema**: *The Data Warehouse Toolkit* by Ralph Kimball
- **API Documentation**: [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)

## 👤 Author

**Your Name**  
[LinkedIn](https://linkedin.com/in/yourprofile) | [Portfolio](https://yourportfolio.com) | [Email](mailto:you@email.com)

*This project was developed to demonstrate skills in data engineering, quantitative analysis, and business intelligence for internship/job applications.*

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Alpha Vantage for providing free financial data API
- Open-source Python data science community
- [Any mentors, courses, or resources that helped]

---

**⭐ If you found this project helpful, please star the repository!**
- [Link to Tableau Dashboard]
