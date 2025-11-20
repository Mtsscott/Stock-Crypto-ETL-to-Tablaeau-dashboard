"""
Alpha Vantage API client for fetching stock and crypto data.
"""
import os
import time
import requests
import pandas as pd
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()


class AlphaVantageClient:
    """Client for interacting with Alpha Vantage API."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_seconds: int = 15):
        """
        Initialize API client.
        
        Args:
            api_key: Alpha Vantage API key (defaults to env variable)
            rate_limit_seconds: Seconds to wait between API calls
        """
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit = rate_limit_seconds
        self.last_call_time = 0
        
        if not self.api_key:
            raise ValueError("API key required. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    def _rate_limit_wait(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            print(f"  ⏳ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        self.last_call_time = time.time()
    
    def fetch_daily_stock(self, ticker: str, outputsize: str = "full") -> Tuple[bool, dict]:
        """
        Fetch daily stock price data.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            outputsize: 'compact' (last 100 days) or 'full' (20+ years)
            
        Returns:
            (success, data_dict) tuple
        """
        self._rate_limit_wait()
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                print(f"  ✗ API Error: {data['Error Message']}")
                return False, {}
            
            if "Note" in data:
                print(f"  ⚠ API Limit: {data['Note']}")
                return False, {}
            
            # Check for data
            data_key = "Time Series (Daily)"
            if data_key not in data:
                print(f"  ⚠ No data available for {ticker}")
                return False, {}
            
            print(f"  ✓ Fetched {len(data[data_key])} records for {ticker}")
            return True, data[data_key]
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Network error: {e}")
            return False, {}
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return False, {}
    
    def fetch_daily_crypto(self, ticker: str, market: str = "USD") -> Tuple[bool, dict]:
        """
        Fetch daily cryptocurrency data.
        
        Args:
            ticker: Crypto ticker (e.g., 'BTC', 'ETH')
            market: Market currency (default 'USD')
            
        Returns:
            (success, data_dict) tuple
        """
        self._rate_limit_wait()
        
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": ticker,
            "market": market,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if "Error Message" in data:
                print(f"  ✗ API Error: {data['Error Message']}")
                return False, {}
            
            if "Note" in data:
                print(f"  ⚠ API Limit: {data['Note']}")
                return False, {}
            
            # Check for data
            data_key = "Time Series (Digital Currency Daily)"
            if data_key not in data:
                print(f"  ⚠ No data available for {ticker}")
                return False, {}
            
            print(f"  ✓ Fetched {len(data[data_key])} records for {ticker}")
            return True, data[data_key]
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Network error: {e}")
            return False, {}
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return False, {}
    
    def fetch_asset(self, ticker: str, asset_type: str) -> Tuple[bool, dict]:
        """
        Fetch data for any asset type (auto-detects stock vs crypto).
        
        Args:
            ticker: Ticker symbol
            asset_type: 'Stock' or 'Crypto'
            
        Returns:
            (success, data_dict) tuple
        """
        if asset_type.lower() == "crypto":
            return self.fetch_daily_crypto(ticker)
        else:
            return self.fetch_daily_stock(ticker)
    
    def process_timeseries(self, ts_data: dict, ticker: str, asset_type: str) -> pd.DataFrame:
        """
        Convert API time series JSON to cleaned DataFrame.
        
        Args:
            ts_data: Time series data from API
            ticker: Ticker symbol
            asset_type: 'Stock' or 'Crypto'
            
        Returns:
            DataFrame with OHLCV data
        """
        df = pd.DataFrame.from_dict(ts_data, orient="index")
        
        # Handle different column naming conventions
        if asset_type.lower() == "crypto":
            df = df.rename(columns={
                "1a. open (USD)": "open",
                "2a. high (USD)": "high",
                "3a. low (USD)": "low",
                "4a. close (USD)": "close",
                "5. volume": "volume"
            })
        else:
            df = df.rename(columns={
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. volume": "volume"
            })
        
        # Select and convert columns
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        
        # Clean up index
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Add metadata
        df["ticker"] = ticker
        df["pct_change"] = df["close"].pct_change() * 100
        
        return df


if __name__ == "__main__":
    # Test the API client
    client = AlphaVantageClient()
    
    print("Testing stock fetch...")
    success, data = client.fetch_daily_stock("AAPL")
    if success:
        df = client.process_timeseries(data, "AAPL", "Stock")
        print(df.head())
    
    print("\nTesting crypto fetch...")
    success, data = client.fetch_daily_crypto("BTC")
    if success:
        df = client.process_timeseries(data, "BTC", "Crypto")
        print(df.head())
