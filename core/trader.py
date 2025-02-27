import time
from typing import Dict, Any, Optional, List
from decimal import Decimal, ROUND_DOWN

from config.settings import TRADING_PAIR
from config.logging_config import logger
from api.coindcx import CoinDCXAPI
from api.discord import DiscordWebhook

class Trader:
    def __init__(self, trading_pair: Optional[str] = None):
        self.trading_pair = trading_pair or TRADING_PAIR
        self.api = CoinDCXAPI()
        self.discord = DiscordWebhook()
        self.active_orders = {}
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        try:
            balances = self.api.get_balance()
            
            # Extract currency from trading pair (e.g., ELYINR -> ELY and INR)
            crypto_currency = self.trading_pair[:3]  # Assuming first 3 chars are crypto
            fiat_currency = self.trading_pair[3:]    # Assuming rest is fiat
            
            result = {
                "crypto": {
                    "currency": crypto_currency,
                    "available": 0,
                    "locked": 0
                },
                "fiat": {
                    "currency": fiat_currency,
                    "available": 0,
                    "locked": 0
                }
            }
            
            # Find the balances for crypto and fiat
            for balance in balances:
                if balance.get("currency") == crypto_currency:
                    result["crypto"]["available"] = float(balance.get("balance", 0))
                    result["crypto"]["locked"] = float(balance.get("locked_balance", 0))
                
                elif balance.get("currency") == fiat_currency:
                    result["fiat"]["available"] = float(balance.get("balance", 0))
                    result["fiat"]["locked"] = float(balance.get("locked_balance", 0))
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            raise
    
    def place_buy_order(self, price: float, quantity: Optional[float] = None, 
                        total_amount: Optional[float] = None) -> Dict[str, Any]:
        """Place a buy order."""
        try:
            # If total_amount is provided, calculate quantity
            if total_amount is not None and quantity is None:
                # Calculate quantity and round down to avoid precision issues
                quantity = Decimal(total_amount) / Decimal(price)
                quantity = float(quantity.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
            
            if quantity is None:
                raise ValueError("Either quantity or total_amount must be provided")
            
            # Place the order
            order = self.api.place_order("buy", self.trading_pair, price, quantity)
            
            # Store the order in active orders
            order_id = order.get("id")
            if order_id:
                self.active_orders[order_id] = {
                    "type": "buy",
                    "price": price,
                    "quantity": quantity,
                    "total": price * quantity,
                    "status": "placed",
                    "timestamp": int(time.time())
                }
            
            # Send Discord notification
            self.discord.send_trade_notification(
                "buy", self.trading_pair, price, quantity, price * quantity, order_id
            )
            
            logger.info(f"Buy order placed: {quantity} {self.trading_pair} at {price}")
            return order
        
        except Exception as e:
            logger.error(f"Error placing buy order: {str(e)}")
            raise
    
    def place_sell_order(self, price: float, quantity: float) -> Dict[str, Any]:
        """Place a sell order."""
        try:
            # Place the order
            order = self.api.place_order("sell", self.trading_pair, price, quantity)
            
            # Store the order in active orders
            order_id = order.get("id")
            if order_id:
                self.active_orders[order_id] = {
                    "type": "sell",
                    "price": price,
                    "quantity": quantity,
                    "total": price * quantity,
                    "status": "placed",
                    "timestamp": int(time.time())
                }
            
            # Send Discord notification
            self.discord.send_trade_notification(
                "sell", self.trading_pair, price, quantity, price * quantity, order_id
            )
            
            logger.info(f"Sell order placed: {quantity} {self.trading_pair} at {price}")
            return order
        
        except Exception as e:
            logger.error(f"Error placing sell order: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            result = self.api.cancel_order(order_id)
            
            if order_id in self.active_orders:
                self.active_orders[order_id]["status"] = "cancelled"
            
            logger.info(f"Order cancelled: {order_id}")
            return result
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of an order."""
        try:
            status = self.api.get_order_status(order_id)
            
            # Update order status in active orders
            if order_id in self.active_orders:
                self.active_orders[order_id]["status"] = status.get("status")
            
            return status
        
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            raise
    
    def update_active_orders(self) -> Dict[str, List[Dict[str, Any]]]:
        """Update the status of all active orders."""
        updated = {"completed": [], "active": []}
        
        for order_id, order_info in list(self.active_orders.items()):
            if order_info["status"] not in ["filled", "cancelled"]:
                try:
                    status = self.get_order_status(order_id)
                    order_status = status.get("status")
                    
                    # Update order status
                    self.active_orders[order_id]["status"] = order_status
                    
                    if order_status in ["filled", "cancelled"]:
                        updated["completed"].append(self.active_orders[order_id])
                    else:
                        updated["active"].append(self.active_orders[order_id])
                
                except Exception as e:
                    logger.error(f"Error updating order {order_id}: {str(e)}")
            
            elif order_info["status"] in ["filled", "cancelled"]:
                updated["completed"].append(order_info)
        
        return updated
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders."""
        return [order for order_id, order in self.active_orders.items() 
                if order["status"] not in ["filled", "cancelled"]]
    
    def get_order_history(self) -> Dict[str, Any]:
        """Get order history from the exchange."""
        try:
            return self.api.get_order_history()
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            raise