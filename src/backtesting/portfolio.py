"""
Portfolio management for backtesting.
"""
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    """Represents a single trade."""
    entry_date: datetime
    entry_price: float
    shares: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    
    @property
    def is_open(self) -> bool:
        """Check if trade is still open."""
        return self.exit_date is None
    
    @property
    def return_pct(self) -> Optional[float]:
        """Calculate trade return percentage."""
        if not self.is_open and self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return None
    
    @property
    def return_dollars(self) -> Optional[float]:
        """Calculate trade return in dollars."""
        if not self.is_open and self.exit_price:
            return (self.exit_price - self.entry_price) * self.shares
        return None
    
    @property
    def holding_days(self) -> Optional[int]:
        """Calculate number of days held."""
        if not self.is_open and self.exit_date:
            return (self.exit_date - self.entry_date).days
        return None


class Portfolio:
    """
    Manages portfolio state during backtesting.
    
    Tracks cash, positions, and trade history.
    """
    
    def __init__(self, starting_capital: float = 10000, commission_pct: float = 0.001):
        """
        Initialize portfolio.
        
        Args:
            starting_capital: Initial cash amount
            commission_pct: Commission as percentage (0.001 = 0.1%)
        """
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.commission_pct = commission_pct
        
        # Position tracking
        self.shares_held = 0.0
        self.position_entry_price = 0.0
        
        # Trade history
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        
        # Performance tracking
        self.equity_curve: List[Dict] = []
    
    def has_position(self) -> bool:
        """Check if currently holding a position."""
        return self.shares_held > 0
    
    def get_position_value(self, current_price: float) -> float:
        """
        Calculate current position value.
        
        Args:
            current_price: Current market price
            
        Returns:
            Total value of position
        """
        return self.shares_held * current_price
    
    def get_total_value(self, current_price: float) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            current_price: Current market price
            
        Returns:
            Cash + position value
        """
        return self.cash + self.get_position_value(current_price)
    
    def buy(self, date: datetime, price: float, shares: Optional[float] = None) -> bool:
        """
        Execute a buy order.
        
        Args:
            date: Trade date
            price: Purchase price
            shares: Number of shares (if None, buy max possible)
            
        Returns:
            True if trade executed, False otherwise
        """
        # Can't buy if already holding position
        if self.has_position():
            return False
        
        # Calculate shares if not specified (use all available cash)
        if shares is None:
            # Account for commission
            shares = (self.cash * (1 - self.commission_pct)) / price
        
        cost = shares * price
        commission = cost * self.commission_pct
        total_cost = cost + commission
        
        # Check if we have enough cash
        if total_cost > self.cash:
            return False
        
        # Execute trade
        self.cash -= total_cost
        self.shares_held = shares
        self.position_entry_price = price
        
        # Record trade
        self.current_trade = Trade(
            entry_date=date,
            entry_price=price,
            shares=shares
        )
        
        return True
    
    def sell(self, date: datetime, price: float) -> bool:
        """
        Execute a sell order.
        
        Args:
            date: Trade date
            price: Sale price
            
        Returns:
            True if trade executed, False otherwise
        """
        # Can't sell if no position
        if not self.has_position():
            return False
        
        # Calculate proceeds
        proceeds = self.shares_held * price
        commission = proceeds * self.commission_pct
        net_proceeds = proceeds - commission
        
        # Execute trade
        self.cash += net_proceeds
        
        # Close out trade record
        if self.current_trade:
            self.current_trade.exit_date = date
            self.current_trade.exit_price = price
            self.trades.append(self.current_trade)
            self.current_trade = None
        
        # Reset position
        self.shares_held = 0.0
        self.position_entry_price = 0.0
        
        return True
    
    def record_day(self, date: datetime, price: float):
        """
        Record daily portfolio state.
        
        Args:
            date: Date
            price: Current price
        """
        self.equity_curve.append({
            'date': date,
            'portfolio_value': self.get_total_value(price),
            'cash': self.cash,
            'position_value': self.get_position_value(price),
            'shares_held': self.shares_held
        })
    
    def get_closed_trades(self) -> List[Trade]:
        """Get list of closed trades."""
        return [t for t in self.trades if not t.is_open]
    
    def get_winning_trades(self) -> List[Trade]:
        """Get list of winning trades."""
        return [t for t in self.get_closed_trades() if t.return_pct and t.return_pct > 0]
    
    def get_losing_trades(self) -> List[Trade]:
        """Get list of losing trades."""
        return [t for t in self.get_closed_trades() if t.return_pct and t.return_pct <= 0]
    
    def get_summary(self) -> Dict:
        """
        Get portfolio summary statistics.
        
        Returns:
            Dictionary with summary stats
        """
        closed_trades = self.get_closed_trades()
        winning_trades = self.get_winning_trades()
        losing_trades = self.get_losing_trades()
        
        final_value = self.equity_curve[-1]['portfolio_value'] if self.equity_curve else self.starting_capital
        
        return {
            'starting_capital': self.starting_capital,
            'final_value': final_value,
            'total_return_pct': ((final_value - self.starting_capital) / self.starting_capital) * 100,
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0,
            'avg_win_pct': sum(t.return_pct for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss_pct': sum(t.return_pct for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        }


if __name__ == "__main__":
    # Test the portfolio
    print("Testing Portfolio...")
    
    from datetime import timedelta
    
    portfolio = Portfolio(starting_capital=10000, commission_pct=0.001)
    
    # Simulate some trades
    start_date = datetime(2023, 1, 1)
    
    # Buy
    portfolio.buy(start_date, price=100)
    print(f"After buy: Cash=${portfolio.cash:.2f}, Shares={portfolio.shares_held:.2f}")
    
    # Hold for 10 days
    for i in range(10):
        portfolio.record_day(start_date + timedelta(days=i), price=100 + i)
    
    # Sell
    portfolio.sell(start_date + timedelta(days=10), price=110)
    print(f"After sell: Cash=${portfolio.cash:.2f}, Shares={portfolio.shares_held:.2f}")
    
    # Summary
    summary = portfolio.get_summary()
    print(f"\nSummary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
