import time
import os
from dotenv import load_dotenv
from api.coindcx import CoinDCXAPI
from api.discord import DiscordWebhook
from core.trader import Trader
from core.tracker import PriceTracker
from config.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Configure logger
logger = setup_logging()

# Trading parameters
TRADING_PAIR = "ELYINR"
BUY_PRICE = 0.65
SELL_PRICE = 0.70
CHECK_INTERVAL = 60  # seconds

def run_strategy():
    """Run the buy at 0.65, sell at 0.7 strategy."""
    logger.info(f"Starting simple trading strategy for {TRADING_PAIR}")
    logger.info(f"Buy at: {BUY_PRICE}, Sell at: {SELL_PRICE}")
    
    # Initialize components
    api = CoinDCXAPI()
    discord = DiscordWebhook()
    trader = Trader(TRADING_PAIR)
    tracker = PriceTracker(TRADING_PAIR)
    
    # Send startup notification
    discord.send_message(f"🚀 Starting ELYINR trading bot (Buy: {BUY_PRICE}, Sell: {SELL_PRICE})")
    
    # Trading state
    in_position = False
    current_order_id = None
    
    try:
        while True:
            try:
                # Get current price
                current_price = tracker.get_current_price()
                logger.info(f"Current price: {current_price}")
                
                # Check if we have a pending order
                if current_order_id:
                    order_status = trader.get_order_status(current_order_id)
                    status = order_status.get("status")
                    
                    if status == "filled":
                        if not in_position:  # Buy order filled
                            logger.info(f"Buy order filled at {BUY_PRICE}")
                            discord.send_message(f"✅ Buy order filled at {BUY_PRICE}!")
                            in_position = True
                        else:  # Sell order filled
                            logger.info(f"Sell order filled at {SELL_PRICE}")
                            discord.send_message(f"💰 Sell order filled at {SELL_PRICE}!")
                            in_position = False
                        
                        current_order_id = None
                    
                    elif status == "cancelled":
                        logger.info(f"Order {current_order_id} was cancelled")
                        current_order_id = None
                    
                    # If order is still open, skip to next iteration
                    if status in ["open", "partially_filled"]:
                        time.sleep(CHECK_INTERVAL)
                        continue
                
                # No active order, check if we should place one
                if not in_position:
                    # If price is at or below buy price, place buy order
                    if current_price <= BUY_PRICE:
                        # Get account balance
                        balance = trader.get_account_balance()
                        available_fiat = balance["fiat"]["available"]
                        
                        # Calculate quantity (use 95% of available balance, up to 1000 INR)
                        total_amount = min(available_fiat * 0.95, 1000)
                        
                        if total_amount > 10:  # Minimum order amount
                            order = trader.place_buy_order(
                                price=current_price,
                                total_amount=total_amount
                            )
                            
                            current_order_id = order.get("id")
                            buy_quantity = total_amount / current_price
                            
                            logger.info(f"Placed buy order at {current_price} for {buy_quantity} {TRADING_PAIR[:3]}")
                            discord.send_message(f"🔵 Placed buy order at {current_price}!")
                        else:
                            logger.warning(f"Insufficient balance for buy order: {available_fiat}")
                            discord.send_message(f"⚠️ Insufficient balance for buy order: {available_fiat}")
                
                else:  # We are in position
                    # If price is at or above sell price, place sell order
                    if current_price >= SELL_PRICE:
                        # Get account balance
                        balance = trader.get_account_balance()
                        available_crypto = balance["crypto"]["available"]
                        
                        if available_crypto > 0:
                            order = trader.place_sell_order(
                                price=current_price,
                                quantity=available_crypto
                            )
                            
                            current_order_id = order.get("id")
                            
                            logger.info(f"Placed sell order at {current_price} for {available_crypto} {TRADING_PAIR[:3]}")
                            discord.send_message(f"🔴 Placed sell order at {current_price}!")
                        else:
                            logger.warning(f"No crypto available for sell order")
                            discord.send_message(f"⚠️ No crypto available for sell order")
            
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                discord.send_message(f"❌ Error in trading loop: {str(e)}")
            
            # Sleep before next check
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("Strategy stopped by user")
        discord.send_message("🛑 Trading bot stopped by user")

if __name__ == "__main__":
    run_strategy()