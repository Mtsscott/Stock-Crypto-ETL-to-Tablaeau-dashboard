"""
Common database queries for loading and saving data.
"""
import pandas as pd
from sqlalchemy import text
from .connection import get_engine


def get_all_tickers() -> pd.DataFrame:
    """
    Get all tickers from dim_ticker.
    
    Returns:
        DataFrame with ticker_id, ticker_symbol, company_name, asset_type
    """
    engine = get_engine()
    query = "SELECT * FROM dim_ticker"
    return pd.read_sql(query, con=engine)


def get_ticker_id(ticker_symbol: str) -> int:
    """
    Get ticker_id for a given ticker symbol.
    
    Args:
        ticker_symbol: Stock/crypto ticker (e.g., 'AAPL', 'BTC')
        
    Returns:
        ticker_id or None if not found
    """
    engine = get_engine()
    query = text("SELECT ticker_id FROM dim_ticker WHERE ticker_symbol = :symbol")
    
    with engine.connect() as conn:
        result = conn.execute(query, {"symbol": ticker_symbol}).fetchone()
        return result[0] if result else None


def get_strategy_id(strategy_name: str) -> int:
    """
    Get strategy_id for a given strategy name.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        strategy_id or None if not found
    """
    engine = get_engine()
    query = text("SELECT strategy_id FROM dim_strategy WHERE strategy_name = :name")
    
    with engine.connect() as conn:
        result = conn.execute(query, {"name": strategy_name}).fetchone()
        return result[0] if result else None


def get_price_data(ticker_symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Get historical price data for a ticker.
    
    Args:
        ticker_symbol: Stock/crypto ticker
        start_date: Optional start date (datetime or string)
        end_date: Optional end date (datetime or string)
        
    Returns:
        DataFrame with dates and OHLCV data
    """
    engine = get_engine()
    
    query = """
        SELECT 
            dd.trade_date,
            fp.open_price,
            fp.high_price,
            fp.low_price,
            fp.close_price,
            fp.volume,
            fp.pct_change
        FROM fact_prices fp
        JOIN dim_ticker dt ON fp.ticker_id = dt.ticker_id
        JOIN dim_date dd ON fp.date_id = dd.date_id
        WHERE dt.ticker_symbol = :symbol
    """
    
    if start_date:
        query += " AND dd.trade_date >= :start_date"
    if end_date:
        query += " AND dd.trade_date <= :end_date"
    
    query += " ORDER BY dd.trade_date"
    
    params = {"symbol": ticker_symbol}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    df = pd.read_sql(text(query), con=engine, params=params)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    
    return df


def get_indicators(ticker_symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Get technical indicators for a ticker.
    
    Args:
        ticker_symbol: Stock/crypto ticker
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with dates and all calculated indicators
    """
    engine = get_engine()
    
    query = """
        SELECT 
            dd.trade_date,
            fti.*
        FROM fact_technical_indicators fti
        JOIN dim_ticker dt ON fti.ticker_id = dt.ticker_id
        JOIN dim_date dd ON fti.date_id = dd.date_id
        WHERE dt.ticker_symbol = :symbol
    """
    
    if start_date:
        query += " AND dd.trade_date >= :start_date"
    if end_date:
        query += " AND dd.trade_date <= :end_date"
    
    query += " ORDER BY dd.trade_date"
    
    params = {"symbol": ticker_symbol}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    df = pd.read_sql(text(query), con=engine, params=params)
    if not df.empty:
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
    
    return df


def get_combined_data(ticker_symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Get price data with indicators joined together.
    
    Args:
        ticker_symbol: Stock/crypto ticker
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with prices and indicators
    """
    prices = get_price_data(ticker_symbol, start_date, end_date)
    indicators = get_indicators(ticker_symbol, start_date, end_date)
    
    if indicators.empty:
        return prices
    
    # Drop duplicate columns from indicators (ticker_id, date_id, indicator_id)
    indicators_clean = indicators.drop(columns=['ticker_id', 'date_id', 'indicator_id'], errors='ignore')
    
    # Join on index (trade_date)
    combined = prices.join(indicators_clean, how='left')
    
    return combined


def save_indicators(df: pd.DataFrame, ticker_symbol: str):
    """
    Save calculated indicators to fact_technical_indicators.
    
    Args:
        df: DataFrame with calculated indicators (must have trade_date index)
        ticker_symbol: Ticker these indicators are for
    """
    engine = get_engine()
    ticker_id = get_ticker_id(ticker_symbol)
    
    if ticker_id is None:
        raise ValueError(f"Ticker {ticker_symbol} not found in database")
    
    # Get date_id mapping
    date_mapping = pd.read_sql(
        "SELECT date_id, trade_date FROM dim_date",
        con=engine
    )
    date_mapping['trade_date'] = pd.to_datetime(date_mapping['trade_date'])
    
    # Prepare data for insert
    df_insert = df.reset_index()
    df_insert['ticker_id'] = ticker_id
    
    # Merge to get date_ids
    df_insert = df_insert.merge(
        date_mapping,
        left_on='trade_date',
        right_on='trade_date',
        how='inner'
    )
    
    # Select only indicator columns
    indicator_cols = [
        'ticker_id', 'date_id',
        'sma_5', 'sma_10', 'sma_20', 'sma_60', 'sma_90', 'sma_200',
        'atr_14', 'std_dev_20',
        'bollinger_upper', 'bollinger_middle', 'bollinger_lower',
        'volume_sma_20', 'volume_ratio',
        'price_vs_sma60_pct', 'distance_from_mean'
    ]
    
    df_final = df_insert[[col for col in indicator_cols if col in df_insert.columns]]
    
    # Insert into database (replace existing)
    # First delete existing records for this ticker
    with engine.begin() as conn:
        delete_query = text("DELETE FROM fact_technical_indicators WHERE ticker_id = :tid")
        conn.execute(delete_query, {"tid": ticker_id})
    
    # Insert new records
    df_final.to_sql(
        'fact_technical_indicators',
        con=engine,
        if_exists='append',
        index=False
    )
    
    print(f"✓ Saved {len(df_final)} indicator records for {ticker_symbol}")


if __name__ == "__main__":
    # Test queries
    print("Testing database queries...")
    
    tickers = get_all_tickers()
    print(f"\nFound {len(tickers)} tickers in database")
    
    if not tickers.empty:
        test_ticker = tickers.iloc[0]['ticker_symbol']
        print(f"\nFetching data for {test_ticker}...")
        
        prices = get_price_data(test_ticker)
        print(f"  Price records: {len(prices)}")
        
        indicators = get_indicators(test_ticker)
        print(f"  Indicator records: {len(indicators)}")
