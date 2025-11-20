"""
Pipeline for calculating and storing technical indicators.
"""
from typing import List, Optional
from ..database.queries import get_all_tickers, get_price_data, save_indicators
from .indicators import calculate_all_indicators, validate_indicators


class FeaturePipeline:
    """Orchestrates indicator calculation for all tickers."""
    
    def __init__(self):
        """Initialize the feature pipeline."""
        pass
    
    def process_ticker(self, ticker_symbol: str, start_date=None, end_date=None) -> bool:
        """
        Calculate and save indicators for a single ticker.
        
        Args:
            ticker_symbol: Ticker to process
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nProcessing {ticker_symbol}...")
            
            # 1. Load price data
            df = get_price_data(ticker_symbol, start_date, end_date)
            
            if df.empty:
                print(f"  ⚠ No price data found for {ticker_symbol}")
                return False
            
            print(f"  Loaded {len(df)} price records")
            
            # 2. Calculate indicators
            df_with_indicators = calculate_all_indicators(df)
            
            # 3. Validate
            if not validate_indicators(df_with_indicators):
                print(f"  ✗ Indicator validation failed")
                return False
            
            # 4. Save to database
            save_indicators(df_with_indicators, ticker_symbol)
            
            print(f"  ✓ Successfully processed {ticker_symbol}")
            return True
            
        except Exception as e:
            print(f"  ✗ Error processing {ticker_symbol}: {e}")
            return False
    
    def process_all_tickers(
        self, 
        ticker_list: Optional[List[str]] = None,
        start_date=None,
        end_date=None
    ) -> dict:
        """
        Calculate indicators for all (or specified) tickers.
        
        Args:
            ticker_list: Optional list of specific tickers to process
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with success/failure counts
        """
        # Get tickers to process
        if ticker_list:
            tickers_df = get_all_tickers()
            tickers_df = tickers_df[tickers_df['ticker_symbol'].isin(ticker_list)]
        else:
            tickers_df = get_all_tickers()
        
        if tickers_df.empty:
            print("No tickers found in database!")
            return {"success": 0, "failed": 0, "total": 0}
        
        print(f"\n{'='*60}")
        print(f"Processing {len(tickers_df)} tickers")
        print(f"{'='*60}")
        
        success_count = 0
        failed_count = 0
        failed_tickers = []
        
        for idx, row in tickers_df.iterrows():
            ticker = row['ticker_symbol']
            
            if self.process_ticker(ticker, start_date, end_date):
                success_count += 1
            else:
                failed_count += 1
                failed_tickers.append(ticker)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Indicator Calculation Complete!")
        print(f"  Success: {success_count}/{len(tickers_df)}")
        print(f"  Failed:  {failed_count}/{len(tickers_df)}")
        
        if failed_tickers:
            print(f"  Failed tickers: {', '.join(failed_tickers)}")
        
        print(f"{'='*60}\n")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(tickers_df),
            "failed_tickers": failed_tickers
        }
    
    def update_recent_indicators(self, days: int = 30) -> dict:
        """
        Update indicators only for recent data (faster than full recalculation).
        
        Args:
            days: Number of recent days to recalculate
            
        Returns:
            Dictionary with processing results
        """
        from datetime import datetime, timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        print(f"Updating indicators for last {days} days (since {start_date.date()})...")
        
        return self.process_all_tickers(start_date=start_date)


if __name__ == "__main__":
    # Test the pipeline
    pipeline = FeaturePipeline()
    
    # Process a single ticker for testing
    result = pipeline.process_ticker("AAPL")
    
    # Uncomment to process all tickers
    # results = pipeline.process_all_tickers()
