"""
Database schema creation and management.
"""
from sqlalchemy import text
from .connection import get_engine


def create_all_tables():
    """
    Create all database tables if they don't exist.
    Safe to run multiple times - only creates missing tables.
    """
    
    engine = get_engine()
    
    tables = {
        "dim_ticker": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_ticker')
            BEGIN
                CREATE TABLE dim_ticker (
                    ticker_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_symbol VARCHAR(10) NOT NULL UNIQUE,
                    company_name VARCHAR(100),
                    asset_type VARCHAR(10)
                );
            END;
        """,
        
        "dim_date": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_date')
            BEGIN
                CREATE TABLE dim_date (
                    date_id INT IDENTITY(1,1) PRIMARY KEY,
                    trade_date DATE NOT NULL UNIQUE,
                    year INT,
                    month INT,
                    day INT,
                    day_of_week VARCHAR(10),
                    quarter INT
                );
            END;
        """,
        
        "fact_prices": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_prices')
            BEGIN
                CREATE TABLE fact_prices (
                    price_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    open_price FLOAT,
                    high_price FLOAT,
                    low_price FLOAT,
                    close_price FLOAT,
                    volume BIGINT,
                    pct_change FLOAT,
                    UNIQUE(ticker_id, date_id)
                );
            END;
        """,
        
        "dim_strategy": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_strategy')
            BEGIN
                CREATE TABLE dim_strategy (
                    strategy_id INT IDENTITY(1,1) PRIMARY KEY,
                    strategy_name VARCHAR(50) NOT NULL UNIQUE,
                    strategy_type VARCHAR(30),
                    strategy_description VARCHAR(500),
                    parameters VARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE()
                );
            END;
        """,
        
        "fact_technical_indicators": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_technical_indicators')
            BEGIN
                CREATE TABLE fact_technical_indicators (
                    indicator_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    sma_5 FLOAT,
                    sma_10 FLOAT,
                    sma_20 FLOAT,
                    sma_60 FLOAT,
                    sma_90 FLOAT,
                    sma_200 FLOAT,
                    atr_14 FLOAT,
                    std_dev_20 FLOAT,
                    bollinger_upper FLOAT,
                    bollinger_middle FLOAT,
                    bollinger_lower FLOAT,
                    volume_sma_20 FLOAT,
                    volume_ratio FLOAT,
                    price_vs_sma60_pct FLOAT,
                    distance_from_mean FLOAT,
                    UNIQUE(ticker_id, date_id)
                );
            END;
        """,
        
        "fact_trading_signals": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_trading_signals')
            BEGIN
                CREATE TABLE fact_trading_signals (
                    signal_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    strategy_id INT FOREIGN KEY REFERENCES dim_strategy(strategy_id),
                    signal_type VARCHAR(10),
                    signal_strength FLOAT,
                    indicator_values VARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE(),
                    UNIQUE(ticker_id, date_id, strategy_id)
                );
            END;
        """,
        
        "fact_trades": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_trades')
            BEGIN
                CREATE TABLE fact_trades (
                    trade_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    strategy_id INT FOREIGN KEY REFERENCES dim_strategy(strategy_id),
                    entry_date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    exit_date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    entry_price FLOAT,
                    exit_price FLOAT,
                    shares FLOAT,
                    trade_return_pct FLOAT,
                    trade_return_dollars FLOAT,
                    holding_days INT,
                    trade_status VARCHAR(10),
                    created_at DATETIME DEFAULT GETDATE()
                );
            END;
        """,
        
        "fact_strategy_performance": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_strategy_performance')
            BEGIN
                CREATE TABLE fact_strategy_performance (
                    performance_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    strategy_id INT FOREIGN KEY REFERENCES dim_strategy(strategy_id),
                    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
                    portfolio_value FLOAT,
                    cash_balance FLOAT,
                    position_value FLOAT,
                    shares_held FLOAT,
                    cumulative_return_pct FLOAT,
                    total_trades INT,
                    winning_trades INT,
                    losing_trades INT,
                    UNIQUE(ticker_id, strategy_id, date_id)
                );
            END;
        """,
        
        "fact_strategy_summary": """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'fact_strategy_summary')
            BEGIN
                CREATE TABLE fact_strategy_summary (
                    summary_id INT IDENTITY(1,1) PRIMARY KEY,
                    ticker_id INT FOREIGN KEY REFERENCES dim_ticker(ticker_id),
                    strategy_id INT FOREIGN KEY REFERENCES dim_strategy(strategy_id),
                    start_date DATE,
                    end_date DATE,
                    final_portfolio_value FLOAT,
                    total_return_pct FLOAT,
                    annualized_return_pct FLOAT,
                    sharpe_ratio FLOAT,
                    max_drawdown_pct FLOAT,
                    volatility FLOAT,
                    total_trades INT,
                    winning_trades INT,
                    losing_trades INT,
                    win_rate_pct FLOAT,
                    avg_win_pct FLOAT,
                    avg_loss_pct FLOAT,
                    profit_factor FLOAT,
                    avg_holding_days FLOAT,
                    calculated_at DATETIME DEFAULT GETDATE(),
                    UNIQUE(ticker_id, strategy_id)
                );
            END;
        """
    }
    
    print("Creating database tables...")
    
    with engine.begin() as conn:
        for table_name, create_sql in tables.items():
            conn.execute(text(create_sql))
            print(f"  ✓ {table_name}")
    
    print("\n✓ All tables ready!\n")


def insert_initial_strategies():
    """
    Insert the predefined trading strategies into dim_strategy.
    Safe to run multiple times - skips duplicates.
    """
    
    engine = get_engine()
    
    strategies = [
        ("SMA Crossover (5/20)", "Momentum", 
         "Buy when 5-day SMA crosses above 20-day SMA, sell when crosses below",
         '{"short_window": 5, "long_window": 20}'),
        
        ("Breakout (60-day)", "Momentum",
         "Buy when price breaks 2% above 60-day SMA, sell when breaks 2% below",
         '{"window": 60, "threshold_pct": 2.0}'),
        
        ("ATR Volatility Breakout", "Volatility",
         "Buy when close exceeds 20-day SMA + 1.5*ATR, sell when below SMA - 1.5*ATR",
         '{"sma_window": 20, "atr_window": 14, "atr_multiplier": 1.5}'),
        
        ("Bollinger Mean Reversion", "Mean Reversion",
         "Buy at lower Bollinger Band, sell at upper band (20-day, 2 SD)",
         '{"window": 20, "num_std": 2.0}'),
        
        ("Volume Momentum", "Volume",
         "Buy when volume > 1.5x average AND price increases, sell opposite",
         '{"volume_window": 20, "volume_multiplier": 1.5}'),
        
        ("Buy and Hold", "Baseline",
         "Buy on first day and hold indefinitely",
         '{"action": "buy_first_day"}')
    ]
    
    insert_sql = """
        IF NOT EXISTS (SELECT 1 FROM dim_strategy WHERE strategy_name = ?)
        BEGIN
            INSERT INTO dim_strategy (strategy_name, strategy_type, strategy_description, parameters)
            VALUES (?, ?, ?, ?)
        END
    """
    
    print("Inserting trading strategies...")
    
    with engine.begin() as conn:
        for name, stype, desc, params in strategies:
            conn.execute(text(insert_sql), (name, name, stype, desc, params))
            print(f"{name}")
    
    print("\n All strategies loaded!\n")


if __name__ == "__main__":
    # Run this file directly to setup database
    create_all_tables()
    insert_initial_strategies()
