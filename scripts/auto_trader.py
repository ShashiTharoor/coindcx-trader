import time
import signal
import sys
from threading import Thread, Event
from typing import Optional

from config.settings import TRADING_PAIR, BUY_PRICE, SELL_PRICE, POLLING_INTERVAL
from config.logging_config import logger
from api.coindcx import CoinDCXAPI
from api.discord import DiscordWebhook
from core.trader import Trader
from core.tracker import PriceTracker

class AutoTrader:
    def __init__(self, trading_pair: Optional[str] = None, 
                 buy_price: Optional[float] = None, 
                 sell_price: Optional[float] = None):
        self.trading_pair = trading_pair or TRADING_PAIR
        self.buy_price = buy_price or BUY_PRICE
        self.sell_price = sell_price or SELL_PRICE
        
        self.trader = Trader(self.trading_pair)
        self.tracker = PriceTracker(self.trading_pair)
        self.discord = DiscordWebhook()
        
        self._running = False
        self._stop_event = Event()
        self._trading_thread = None
        
        # Trading state
        self.in_position = False
        self.current_order_id = None
        self.buy_order_price = None
        self.buy_order_quantity = None
    
    def check_price_and_trade(self, current_price: float) -> None:
        """Check current price and execute trading strategy."""
        logger.info(f"Current price: {current_price}, Buy price: {self.buy_price}, Sell price: {self.sell_price}")
        
        # Update order status if there's an active order
        if self.current_order_id:
            try:
                order_status = self.trader.get_order_status(self.current_order_id)
                status = order_status.get("status")
                
                if status == "filled":
                    if not self.in_position:  # Buy order filled
                        logger.info(f"Buy order filled at {self.buy_order_price}")
                        self.in_position = True
                        self.discord.send_message(f"🟢 Buy order filled at {self.buy_order_price}!")
                        self.current_order_id = None
                    else:  # Sell order filled
                        logger.info(f"Sell order filled at {self.sell_price}")
                        self.in_position = False
                        self.discord.send_message(f"🔴 Sell order filled at {self.sell_price}!")
                        self.current_order_id = None
                
                elif status == "cancelled":
                    logger.info(f"Order {self.current_order_id} was cancelled")
                    self.current_order_id = None
                
                # If order is still open, don't do anything else
                if status in ["open", "partially_filled"]:
                    return
            
            except Exception as e:
                logger.error(f"Error checking order status: {str(e)}")
        
        # No active order, check if we should place one
        if not self.in_position and not self.current_order_id:
            # If price is at or below buy price, place buy order
            if current_price <= self.buy_price:
                try:
                    # Get account balance to determine how much to buy
                    balance = self.trader.get_account_balance()
                    available_fiat = balance["fiat"]["available"]
                    
                    # Calculate quantity based on available balance (use 95% to account for fees)
                    total_amount = min(available_fiat * 0.95, 1000)  # Limit to 1000 INR per trade
                    
                    if total_amount > 10:  # Minimum order amount
                        order = self.trader.place_buy_order(
                            price=current_price,
                            total_amount=total_amount
                        )
                        
                        self.current_order_id = order.get("id")
                        self.buy_order_price = current_price
                        self.buy_order_quantity = total_amount / current_price
                        
                        logger.info(f"Placed buy order at {current_price} for {self.buy_order_quantity} {self.trading_pair[:3]}")
                        self.discord.send_message(f"📈 Placed buy order at {current_price}!")
                    else:
                        logger.warning(f"Insufficient balance for buy order: {available_fiat}")
                
                except Exception as e:
                    logger.error(f"Error placing buy order: {str(e)}")
        
        elif self.in_position and not self.current_order_id:
            # If price is at or above sell price, place sell order
            if current_price >= self.sell_price:
                try:
                    # Get account balance to determine how much to sell
                    balance = self.trader.get_account_balance()
                    available_crypto = balance["crypto"]["available"]
                    
                    if available_crypto > 0:
                        order = self.trader.place_sell_order(
                            price=current_price,
                            quantity=available_crypto
                        )
                        
                        self.current_order_id = order.get("id")
                        
                        logger.info(f"Placed sell order at {current_price} for {available_crypto} {self.trading_pair[:3]}")
                        self.discord.send_message(f"📉 Placed sell order at {current_price}!")
                    else:
                        logger.warning(f"No crypto available for sell order")
                
                except Exception as e:
                    logger.error(f"Error placing sell order: {str(e)}")
    
    def start_trading(self) -> None:
        """Start the automated trading process."""
        if self._running:
            logger.warning("Auto trader is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        def trading_loop():
            logger.info(f"Starting auto trader for {self.trading_pair}")
            logger.info(f"Strategy: Buy at {self.buy_price}, Sell at {self.sell_price}")
            
            try:
                while not self._stop_event.is_set():
                    current_price = self.tracker.get_current_price()
                    self.check_price_and_trade(current_price)
                    self._stop_event.wait(POLLING_INTERVAL)
            
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
            finally:
                self._running = False
                logger.info("Auto trader stopped")
        
        self._trading_thread = Thread(target=trading_loop)
        self._trading_thread.daemon = True
        self._trading_thread.start()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def stop_trading(self) -> None:
        """Stop the automated trading process."""
        if not self._running:
            logger.warning("Auto trader is not running")
            return
        
        logger.info("Stopping auto trader...")
        self._stop_event.set()
        
        if self._trading_thread:
            self._trading_thread.join(timeout=5)
        
        self._running = False
    
    def _signal_handler(self, sig, frame) -> None:
        """Handle termination signals."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_trading()
        sys.exit(0)

# Run auto trader if script is executed directly
if __name__ == "__main__":
    trader = AutoTrader()
    trader.start_trading()
    
    try:
        # Keep the main thread alive
        while trader._running:
            time.sleep(1)
    except KeyboardInterrupt:
        trader.stop_trading()