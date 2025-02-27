import time
import json
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional

from config.settings import COINDCX_API_KEY, COINDCX_API_SECRET, MAX_RETRIES, RETRY_DELAY
from config.logging_config import logger

class CoinDCXAPI:
    BASE_URL = "https://api.coindcx.com"
    
    def __init__(self):
        self.api_key = COINDCX_API_KEY
        self.api_secret = COINDCX_API_SECRET
        
        if not self.api_key or not self.api_secret:
            raise ValueError("CoinDCX API credentials not found. Please check your environment variables.")
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for API authentication."""
        payload_str = json.dumps(payload).encode('utf-8')
        return hmac.new(self.api_secret.encode('utf-8'), payload_str, hashlib.sha256).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, 
                      auth_required: bool = False) -> Dict[str, Any]:
        """Make API request with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        
        if auth_required:
            if payload is None:
                payload = {}
            
            # Add timestamp to payload
            payload["timestamp"] = int(time.time() * 1000)
            
            # Generate signature
            signature = self._generate_signature(payload)
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "X-AUTH-APIKEY": self.api_key,
                "X-AUTH-SIGNATURE": signature
            }
        
        for attempt in range(MAX_RETRIES):
            try:
                if method.lower() == "get":
                    response = requests.get(url, headers=headers, params=payload)
                elif method.lower() == "post":
                    response = requests.post(url, headers=headers, json=payload)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise
    
    def get_market_data(self, market: str) -> Dict[str, Any]:
        """Get market data for a specific trading pair."""
        endpoint = "/v1/markets_details"
        response = self._make_request("GET", endpoint)
        
        # Find the specific market data
        for market_data in response:
            if market_data.get("symbol") == market:
                return market_data
        
        raise ValueError(f"Market {market} not found")
    
    def get_ticker(self, market: str) -> Dict[str, Any]:
        """Get current ticker information."""
        endpoint = "/v1/ticker"
        response = self._make_request("GET", endpoint)
        
        # Find the specific ticker
        for ticker in response:
            if ticker.get("market") == market:
                return ticker
        
        raise ValueError(f"Ticker for market {market} not found")
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        endpoint = "/v1/balances"
        return self._make_request("POST", endpoint, {}, auth_required=True)
    
    def place_order(self, side: str, market: str, price: float, quantity: float) -> Dict[str, Any]:
        """Place a limit order."""
        endpoint = "/v1/orders/create"
        
        payload = {
            "side": side.lower(),  # buy or sell
            "order_type": "limit_order",
            "market": market,
            "price_per_unit": price,
            "total_quantity": quantity,
            "client_order_id": f"{int(time.time() * 1000)}",
        }
        
        return self._make_request("POST", endpoint, payload, auth_required=True)
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of an order."""
        endpoint = "/v1/orders/status"
        
        payload = {
            "id": order_id
        }
        
        return self._make_request("POST", endpoint, payload, auth_required=True)
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        endpoint = "/v1/orders/cancel"
        
        payload = {
            "id": order_id
        }
        
        return self._make_request("POST", endpoint, payload, auth_required=True)
    
    def get_order_history(self) -> Dict[str, Any]:
        """Get order history."""
        endpoint = "/v1/orders/trade_history"
        return self._make_request("POST", endpoint, {}, auth_required=True)