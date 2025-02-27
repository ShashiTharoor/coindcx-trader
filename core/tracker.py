import time
from typing import Dict, Any, Optional, Callable

from config.settings import POLLING_INTERVAL, TRADING_PAIR
from config.logging_config import logger
from api.coindcx import CoinDCXAPI

class PriceTracker:
    def __init__(self, trading_pair: Optional[str] = None):
        self.trading_pair = trading_pair or TRADING_PAIR
        self.api = CoinDCXAPI()
        self.current_price = None
        self.price_history = []
        self.callbacks = []
        self._running = False
    
    def get_current_price(self) -> float:
        """Get the current price of the trading pair."""
        try:
            ticker = self.api.get_ticker(self.trading_pair)
            price = float(ticker.get("last_price", 0))
            self.current_price = price
            return price
        
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            return self.current_price or 0
    
    def register_callback(self, callback: Callable[[float], None]) -> None:
        """Register a callback function to be called when price is updated."""
        self.callbacks.append(callback)
    
    def start_tracking(self, interval: Optional[int] = None) -> None:
        """Start tracking price at regular intervals."""
        tracking_interval = interval or POLLING_INTERVAL
        self._running = True
        
        logger.info(f"Starting price tracking for {self.trading_pair} at {tracking_interval}s intervals")
        
        try:
            while self._running:
                price = self.get_current_price()
                
                # Store price in history (limit to last 1000 data points)
                timestamp = int(time.time())
                self.price_history.append({"timestamp": timestamp, "price": price})
                if len(self.price_history) > 1000:
                    self.price_history.pop(0)
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(price)
                    except Exception as e:
                        logger.error(f"Error in price callback: {str(e)}")
                
                time.sleep(tracking_interval)
        
        except KeyboardInterrupt:
            logger.info("Price tracking stopped by user")
        finally:
            self._running = False
    
    def stop_tracking(self) -> None:
        """Stop tracking price."""
        self._running = False
        logger.info(f"Stopping price tracking for {self.trading_pair}")
    
    def get_price_history(self, limit: Optional[int] = None) -> list:
        """Get the price history."""
        if limit and limit < len(self.price_history):
            return self.price_history[-limit:]
        return self.price_history
    
    def get_price_change_24h(self) -> Dict[str, Any]:
        """Get 24-hour price change information."""
        try:
            ticker = self.api.get_ticker(self.trading_pair)
            return {
                "price": float(ticker.get("last_price", 0)),
                "change_24h": float(ticker.get("change_24h", 0)),
                "high_24h": float(ticker.get("high_24h", 0)),
                "low_24h": float(ticker.get("low_24h", 0)),
                "volume_24h": float(ticker.get("volume_24h", 0))
            }
        except Exception as e:
            logger.error(f"Error getting 24h price change: {str(e)}")
            return {
                "price": self.current_price or 0,
                "change_24h": 0,
                "high_24h": 0,
                "low_24h": 0,
                "volume_24h": 0
            }