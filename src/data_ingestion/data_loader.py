"""
Load price data from API into database.
"""
import pandas as pd
from sqlalchemy import text
from typing import Dict
from ..database.connection import get_engine


class PriceDataLoader:
    """Handles loading price data into the database."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.engine = get_engine()
        self.lookups = self._load_lookups()
    
    def _load_lookups(self) -> Dict[str, pd.DataFrame]:
        """
        Load dimension table lookups for faster inserts.
        
        Returns:
            Dictionary with ticker, date, and existing price lookups
        """
        return {
            "tickers": pd.read_sql("SELECT * FROM dim_ticker", con=self.engine),
            "dates": pd.read_sql(
                "SELECT * FROM dim_date", 
                con=self.engine
            ).assign(trade_date=lambda x: pd.to_datetime(x["trade_date"])),
            "existing_prices": pd.read_sql(
                "SELECT DISTINCT ticker_id, date_id FROM fact_prices",
                con=self.engine
            )
        }
    
    def refresh_lookups(self):
        """Refresh cached lookups after inserting new data."""
        self.lookups = self._load_lookups()
    
    def insert_ticker_if_new(self, ticker: str, company_name: str, asset_type: str) -> int:
        """
        Insert ticker into dim_ticker if it doesn't exist.
        
        Args:
            ticker: Ticker symbol
            company_name: Full company/asset name
            asset_type: 'Stock' or 'Crypto'
            
        Returns:
            ticker_id (existing or newly created)
        """
        # Check if ticker exists
        existing = self.lookups["tickers"][
            self.lookups["tickers"]["ticker_symbol"] == ticker
        ]
        
        if not existing.empty:
            return existing.iloc[0]["ticker_id"]
        
        # Insert new ticker
        df_ticker = pd.DataFrame({
            "ticker_symbol": [ticker],
            "company_name": [company_name],
            "asset_type": [asset_type]
        })
        
        df_ticker.to_sql("dim_ticker", con=self.engine, if_exists="append", index=False)
        
        # Refresh lookups
        self.lookups["tickers"] = pd.read_sql("SELECT * FROM dim_ticker", con=self.engine)
        
        # Get the new ticker_id
        ticker_id = self.lookups["tickers"][
            self.lookups["tickers"]["ticker_symbol"] == ticker
        ].iloc[0]["ticker_id"]
        
        print(f"  + Added new ticker: {ticker} (ID: {ticker_id})")
        return ticker_id
    
    def insert_new_dates(self, df: pd.DataFrame) -> int:
        """
        Insert new dates from DataFrame into dim_date.
        
        Args:
            df: DataFrame with DatetimeIndex
            
        Returns:
            Number of new dates inserted
        """
        df_dates = pd.DataFrame({
            "trade_date": df.index,
            "year": df.index.year.astype(int),
            "month": df.index.month.astype(int),
            "day": df.index.day.astype(int),
            "day_of_week": df.index.day_name(),
            "quarter": df.index.quarter.astype(int)
        })
        
        # Find new dates
        new_dates = df_dates[
            ~df_dates["trade_date"].isin(self.lookups["dates"]["trade_date"])
        ]
        
        if not new_dates.empty:
            new_dates.to_sql("dim_date", con=self.engine, if_exists="append", index=False)
            
            # Refresh lookups
            self.lookups["dates"] = pd.read_sql(
                "SELECT * FROM dim_date", 
                con=self.engine
            ).assign(trade_date=lambda x: pd.to_datetime(x["trade_date"]))
            
            print(f"  + Added {len(new_dates)} new dates")
            return len(new_dates)
        
        return 0
    
    def insert_price_data(self, df: pd.DataFrame, ticker: str, ticker_id: int) -> int:
        """
        Insert price data into fact_prices.
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Ticker symbol
            ticker_id: ID from dim_ticker
            
        Returns:
            Number of new records inserted
        """
        # Prepare price data
        df_prices = pd.DataFrame({
            "trade_date": df.index,
            "open_price": df["open"],
            "high_price": df["high"],
            "low_price": df["low"],
            "close_price": df["close"],
            "volume": df["volume"].astype('int64'),
            "pct_change": df["pct_change"],
        }).assign(trade_date=lambda x: pd.to_datetime(x["trade_date"]))
        
        # Join with dimension tables to get IDs
        df_prices = (
            df_prices
            .assign(ticker_id=ticker_id)
            .merge(
                self.lookups["dates"][["date_id", "trade_date"]],
                on="trade_date",
                how="left"
            )
            [[
                "ticker_id", "date_id", "open_price", "high_price",
                "low_price", "close_price", "volume", "pct_change"
            ]]
        )
        
        # Filter out existing records to avoid duplicates
        merged = df_prices.merge(
            self.lookups["existing_prices"],
            on=["ticker_id", "date_id"],
            how="left",
            indicator=True
        )
        
        new_facts = merged[merged["_merge"] == "left_only"].drop(columns="_merge")
        
        if not new_facts.empty:
            new_facts.to_sql("fact_prices", con=self.engine, if_exists="append", index=False)
            
            # Refresh existing prices lookup
            self.lookups["existing_prices"] = pd.read_sql(
                "SELECT DISTINCT ticker_id, date_id FROM fact_prices",
                con=self.engine
            )
            
            print(f" Inserted {len(new_facts)} new price records")
            return len(new_facts)
        
        print(f" No new records (all data already exists)")
        return 0
    
    def load_asset(self, df: pd.DataFrame, ticker: str, company_name: str, asset_type: str) -> int:
        """
        Complete loading pipeline for one asset.
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Ticker symbol
            company_name: Company/asset name
            asset_type: 'Stock' or 'Crypto'
            
        Returns:
            Number of new price records inserted
        """
        # 1. Ensure ticker exists
        ticker_id = self.insert_ticker_if_new(ticker, company_name, asset_type)
        
        # 2. Insert any new dates
        self.insert_new_dates(df)
        
        # 3. Insert price data
        new_records = self.insert_price_data(df, ticker, ticker_id)
        
        return new_records
    
    def get_existing_date_range(self, ticker: str) -> tuple:
        """
        Get the date range of existing data for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            (min_date, max_date) tuple or (None, None) if no data
        """
        query = text("""
            SELECT 
                MIN(dd.trade_date) as min_date,
                MAX(dd.trade_date) as max_date
            FROM fact_prices fp
            JOIN dim_ticker dt ON fp.ticker_id = dt.ticker_id
            JOIN dim_date dd ON fp.date_id = dd.date_id
            WHERE dt.ticker_symbol = :ticker
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"ticker": ticker}).fetchone()
            
            if result and result[0]:
                return result[0], result[1]
            return None, None
    
    def get_data_stats(self) -> pd.DataFrame:
        """
        Get summary statistics of loaded data.
        
        Returns:
            DataFrame with record counts per ticker
        """
        query = """
            SELECT 
                dt.ticker_symbol,
                dt.asset_type,
                COUNT(*) as record_count,
                MIN(dd.trade_date) as earliest_date,
                MAX(dd.trade_date) as latest_date,
                DATEDIFF(day, MIN(dd.trade_date), MAX(dd.trade_date)) as days_span
            FROM fact_prices fp
            JOIN dim_ticker dt ON fp.ticker_id = dt.ticker_id
            JOIN dim_date dd ON fp.date_id = dd.date_id
            GROUP BY dt.ticker_symbol, dt.asset_type
            ORDER BY dt.asset_type, dt.ticker_symbol
        """
        
        return pd.read_sql(query, con=self.engine)


if __name__ == "__main__":
    # Test the data loader
    loader = PriceDataLoader()
    
    print("Current data in database:")
    stats = loader.get_data_stats()
    print(stats)
