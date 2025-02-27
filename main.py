import argparse
import sys
import time
from threading import Thread

from config.settings import TRADING_PAIR, BUY_PRICE, SELL_PRICE, PRICE_ALERT_THRESHOLDS
from config.logging_config import logger, setup_logging
from scripts.auto_trader import AutoTrader
from scripts.price_alerts import run_price_alerts
from core.tracker import PriceTracker
from core.alerts import AlertSystem
from core.trader import Trader
from api.coindcx import CoinDCXAPI
from api.discord import DiscordWebhook

def check_api_connection():
    """Check if API connection is working."""
    try:
        api = CoinDCXAPI()
        api.get_ticker(TRADING_PAIR)
        return True
    except Exception as e:
        logger.error(f"API connection failed: {str(e)}")
        return False

def check_discord_connection():
    """Check if Discord webhook is working."""
    try:
        discord = DiscordWebhook()
        discord.send_message("🔄 Crypto Manager system started")
        return True
    except Exception as e:
        logger.error(f"Discord connection failed: {str(e)}")
        return False

def run_all():
    """Run all components of the application."""
    logger.info("Starting all components of the Crypto Manager system")
    
    # Check connections
    if not check_api_connection():
        logger.error("Failed to connect to CoinDCX API. Exiting...")
        sys.exit(1)
    
    if not check_discord_connection():
        logger.warning("Failed to connect to Discord webhook. Continuing without notifications...")
    
    # Create shared price tracker
    tracker = PriceTracker(TRADING_PAIR)
    
    # Create alert system with shared tracker
    alert_system = AlertSystem(TRADING_PAIR, PRICE_ALERT_THRESHOLDS, tracker)
    
    # Create auto trader
    auto_trader = AutoTrader(TRADING_PAIR, BUY_PRICE, SELL_PRICE)
    
    # Start tracker in a separate thread
    tracker_thread = Thread(target=tracker.start_tracking)
    tracker_thread.daemon = True
    tracker_thread.start()
    
    # Start alert monitoring using the shared tracker
    alert_system.start_monitoring(use_existing_tracker=True)
    
    # Start auto trader
    auto_trader.start_trading()
    
    logger.info("All components started successfully")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Crypto Manager system...")
        auto_trader.stop_trading()
        alert_system.stop_monitoring()
        tracker.stop_tracking()

def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(description="Crypto Manager - ELYINR Trading System")
    
    # Define command-line arguments
    parser.add_argument("--mode", choices=["all", "trader", "alerts", "info"], 
                        default="all", help="Operation mode")
    parser.add_argument("--buy-price", type=float, help="Buy price threshold")
    parser.add_argument("--sell-price", type=float, help="Sell price threshold")
    parser.add_argument("--high-alert", type=float, help="High price alert threshold")
    parser.add_argument("--low-alert", type=float, help="Low price alert threshold")
    
    args = parser.parse_args()
    
    # Configure logger
    setup_logging()
    
    # Override settings with command line arguments if provided
    buy_price = args.buy_price or BUY_PRICE
    sell_price = args.sell_price or SELL_PRICE
    
    thresholds = PRICE_ALERT_THRESHOLDS.copy()
    if args.high_alert:
        thresholds["high"] = args.high_alert
    if args.low_alert:
        thresholds["low"] = args.low_alert
    
    # Run in the specified mode
    if args.mode == "all":
        run_all()
    
    elif args.mode == "trader":
        logger.info("Starting in trader mode")
        trader = AutoTrader(TRADING_PAIR, buy_price, sell_price)
        trader.start_trading()
        
        try:
            while trader._running:
                time.sleep(1)
        except KeyboardInterrupt:
            trader.stop_trading()
    
    elif args.mode == "alerts":
        logger.info("Starting in alerts mode")
        run_price_alerts(TRADING_PAIR, thresholds)
    
    elif args.mode == "info":
        logger.info("Starting in info mode")
        
        # Display current market information
        api = CoinDCXAPI()
        ticker = api.get_ticker(TRADING_PAIR)
        
        print("\n===== ELYINR Market Information =====")
        print(f"Current Price: {ticker.get('last_price')}")
        print(f"24h High: {ticker.get('high_24h')}")
        print(f"24h Low: {ticker.get('low_24h')}")
        print(f"24h Volume: {ticker.get('volume_24h')}")
        print(f"24h Change: {ticker.get('change_24h')}%")
        
        # Display current strategy settings
        print("\n===== Trading Strategy =====")
        print(f"Buy Price: {buy_price}")
        print(f"Sell Price: {sell_price}")
        print(f"Alert Thresholds: {thresholds}")
        
        # Check account balance if possible
        try:
            trader = Trader(TRADING_PAIR)
            balance = trader.get_account_balance()
            
            print("\n===== Account Balance =====")
            print(f"Crypto ({balance['crypto']['currency']}): {balance['crypto']['available']} (Available) + {balance['crypto']['locked']} (Locked)")
            print(f"Fiat ({balance['fiat']['currency']}): {balance['fiat']['available']} (Available) + {balance['fiat']['locked']} (Locked)")
        except Exception as e:
            print(f"\nCould not retrieve account balance: {str(e)}")

if __name__ == "__main__":
    main()