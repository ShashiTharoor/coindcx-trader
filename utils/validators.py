import re
from typing import Optional, Dict, Any, Union

def validate_api_credentials(api_key: str, api_secret: str) -> bool:
    """Validate API credentials format."""
    if not api_key or not api_secret:
        return False
    
    # Check if API key and secret have reasonable lengths
    if len(api_key) < 10 or len(api_secret) < 10:
        return False
    
    return True

def validate_webhook_url(url: str) -> bool:
    """Validate Discord webhook URL format."""
    if not url:
        return False
    
    # Basic pattern for Discord webhook URLs
    pattern = r'^https://discord\.com/api/webhooks/\d+/[\w-]+$'
    return bool(re.match(pattern, url))

def validate_trading_pair(pair: str) -> bool:
    """Validate trading pair format."""
    if not pair or len(pair) < 5:
        return False
    
    # Common pattern for trading pairs (e.g., BTCUSDT, ELYINR)
    pattern = r'^[A-Z]{2,5}[A-Z]{2,5}$'
    return bool(re.match(pattern, pair))

def validate_price(price: Union[float, str]) -> bool:
    """Validate price value."""
    try:
        price_float = float(price)
        return price_float > 0
    except (ValueError, TypeError):
        return False

def validate_quantity(quantity: Union[float, str]) -> bool:
    """Validate quantity value."""
    try:
        quantity_float = float(quantity)
        return quantity_float > 0
    except (ValueError, TypeError):
        return False

def validate_order_params(params: Dict[str, Any]) -> Dict[str, str]:
    """Validate order parameters."""
    errors = {}
    
    # Check required fields
    required_fields = ["side", "market", "price", "quantity"]
    for field in required_fields:
        if field not in params:
            errors[field] = f"Missing required field: {field}"
    
    # Validate side
    if "side" in params and params["side"] not in ["buy", "sell"]:
        errors["side"] = "Side must be 'buy' or 'sell'"
    
    # Validate market
    if "market" in params and not validate_trading_pair(params["market"]):
        errors["market"] = "Invalid trading pair format"
    
    # Validate price
    if "price" in params and not validate_price(params["price"]):
        errors["price"] = "Price must be a positive number"
    
    # Validate quantity
    if "quantity" in params and not validate_quantity(params["quantity"]):
        errors["quantity"] = "Quantity must be a positive number"
    
    return errors