import time
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

def format_price(price: float, decimals: int = 8) -> str:
    """Format price with appropriate decimals."""
    return f"{price:.{decimals}f}"

def calculate_profit_loss(buy_price: float, sell_price: float, 
                          quantity: float, fee_percentage: float = 0.1) -> Dict[str, Any]:
    """Calculate profit/loss for a trade."""
    buy_total = buy_price * quantity
    buy_fee = buy_total * (fee_percentage / 100)
    
    sell_total = sell_price * quantity
    sell_fee = sell_total * (fee_percentage / 100)
    
    gross_profit = sell_total - buy_total
    net_profit = gross_profit - buy_fee - sell_fee
    
    profit_percentage = (net_profit / buy_total) * 100
    
    return {
        "buy_price": buy_price,
        "sell_price": sell_price,
        "quantity": quantity,
        "buy_total": buy_total,
        "sell_total": sell_total,
        "buy_fee": buy_fee,
        "sell_fee": sell_fee,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "profit_percentage": profit_percentage
    }

def save_to_json(data: Any, filename: str) -> bool:
    """Save data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")
        return False

def load_from_json(filename: str) -> Any:
    """Load data from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading from JSON: {str(e)}")
        return None

def timestamp_to_datetime(timestamp: int) -> str:
    """Convert Unix timestamp to datetime string."""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def calculate_moving_average(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate simple moving average."""
    if len(prices) < period:
        return None
    
    return sum(prices[-period:]) / period

def calculate_exponential_moving_average(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate exponential moving average."""
    if len(prices) < period:
        return None
    
    # First EMA is just the SMA
    ema = sum(prices[:period]) / period
    
    # Calculate multiplier
    multiplier = 2 / (period + 1)
    
    # Calculate EMA for the rest of the data points
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(prices) <= period:
        return None
    
    # Calculate price changes
    changes = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    
    # Get gains and losses
    gains = [change if change > 0 else 0 for change in changes]
    losses = [abs(change) if change < 0 else 0 for change in changes]
    
    # Calculate average gain and loss
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100  # No losses, RSI is 100
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi