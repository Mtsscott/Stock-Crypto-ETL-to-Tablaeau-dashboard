#!/usr/bin/env python3
"""
Fetch latest price data from Alpha Vantage API and load into database.

Usage:
    python scripts/fetch_latest_data.py
"""
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_ingestion.api_client import AlphaVantageClient
from src.data_ingestion.data_loader import PriceDataLoader

# Asset definitions
ASSETS = {
    # Stocks
    "WMT":   {"company_name": "Walmart Inc.",             "asset_type": "Stock"},
    "AAPL":  {"company_name": "Apple Inc.",               "asset_type": "Stock"},
    "MSFT":  {"company_name": "Microsoft Corp.",          "asset_type": "Stock"},
    "AMZN":  {"company_name": "Amazon.com Inc.",          "asset_type": "Stock"},
    "GOOGL": {"company_name": "Alphabet Inc.",            "asset_type": "Stock"},
    "META":  {"company_name": "Meta Platforms Inc.",      "asset_type": "Stock"},
    "TSLA":  {"company_name": "Tesla Inc.",               "asset_type": "Stock"},
    "NFLX":  {"company_name": "Netflix Inc.",             "asset_type": "Stock"},
    "JPM":   {"company_name": "JPMorgan Chase & Co.",     "asset_type": "Stock"},
    "NVDA":  {"company_name": "NVIDIA Corp.",             "asset_type": "Stock"},
    
    # Cryptocurrencies
    "BTC":   {"company_name": "Bitcoin",                  "asset_type": "Crypto"},
    "ETH":   {"company_name": "Ethereum",                 "asset_type": "Crypto"},
    "ADA":   {"company_name": "Cardano",                  "asset_type": "Crypto"},
    "SOL":   {"company_name": "Solana",                   "asset_type": "Crypto"},
    "XRP":   {"company_name": "Ripple",                   "asset_type": "Crypto"},
    "DOGE":  {"company_name": "Dogecoin",                 "asset_type": "Crypto"},
    "LTC":   {"company_name": "Litecoin",                 "asset_type": "Crypto"},
    "DOT":   {"company_name": "Polkadot",                 "asset_type": "Crypto"},
    "AVAX":  {"company_name": "Avalanche",                "asset_type": "Crypto"},
    "BNB":   {"company_name": "Binance Coin",             "asset_type": "Crypto"}
}


def main():
    """Main execution function."""
    print(f"{'='*70}")
    print(f"Stock & Crypto Data Update")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Initialize API client and data loader
    client = AlphaVantageClient(rate_limit_seconds=15)
    loader = PriceDataLoader()
    
    tickers = list(ASSETS.keys())
    success_count = 0
    error_count = 0
    total_records = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # Get asset info
            company_name = ASSETS[ticker]["company_name"]
            asset_type = ASSETS[ticker]["asset_type"]
            
            # Check existing data
            min_date, max_date = loader.get_existing_date_range(ticker)
            if max_date:
                print(f"  Existing data: {min_date.date()} to {max_date.date()}")
            
            # Fetch from API
            success, ts_data = client.fetch_asset(ticker, asset_type)
            
            if not success:
                error_count += 1
                continue
            
            # Process data
            df = client.process_timeseries(ts_data, ticker, asset_type)
            
            # Load into database
            new_records = loader.load_asset(df, ticker, company_name, asset_type)
            
            total_records += new_records
            success_count += 1
            
            print()
            
        except Exception as e:
            print(f" Error: {e}")
            error_count += 1
        
        # Rate limiting happens in client
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"Data Update Complete!")
    print(f"  Success: {success_count}/{len(tickers)}")
    print(f"  Errors:  {error_count}/{len(tickers)}")
    print(f"  New records: {total_records}")
    print(f"{'='*70}\n")
    
    # Show current database stats
    print("Current database statistics:")
    stats = loader.get_data_stats()
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
