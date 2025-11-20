"""
Calculate technical indicators for all tickers in database.

Usage:
    python scripts/calculate_indicators.py
    python scripts/calculate_indicators.py --ticker AAPL  # Single ticker
    python scripts/calculate_indicators.py --recent 30    # Last 30 days only
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.feature_pipeline import FeaturePipeline


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Calculate technical indicators')
    parser.add_argument(
        '--ticker',
        type=str,
        help='Process single ticker only (e.g., AAPL)'
    )
    parser.add_argument(
        '--recent',
        type=int,
        help='Process only recent N days'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = FeaturePipeline()
    
    # Run based on arguments
    if args.ticker:
        # Single ticker
        pipeline.process_ticker(args.ticker)
    
    elif args.recent:
        # Recent data only
        pipeline.update_recent_indicators(days=args.recent)
    
    else:
        # All tickers, full history
        pipeline.process_all_tickers()


if __name__ == "__main__":
    main()
