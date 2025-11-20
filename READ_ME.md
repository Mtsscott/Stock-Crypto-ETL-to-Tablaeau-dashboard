# Stock & Crypto Trading Strategy Backtesting System

## Overview
Built a data warehouse and backtesting framework to evaluate 6 trading 
strategies across 20+ assets (stocks & cryptocurrencies). Designed star 
schema in SQL Server, developed ETL pipelines in Python, and created 
interactive Tableau dashboards.

## Key Features
- Automated data ingestion from Alpha Vantage API
- 15+ technical indicators (SMA, RSI, Bollinger Bands, ATR)
- 6 backtested strategies with performance metrics
- Interactive Tableau dashboards

## Tech Stack
Python | SQL Server | Tableau | SQLAlchemy | Pandas

## Quick Start
1. Clone repo: `git clone ...`
2. Install: `pip install -r requirements.txt`
3. Setup DB: `python scripts/setup_database.py`
4. Run: `python scripts/run_backtests.py`

## Results
- Best performer: Bollinger Mean Reversion (34% return vs 22% buy-hold)
- Sharpe ratio improved 40% with volatility strategies
- [Link to Tableau Dashboard]
