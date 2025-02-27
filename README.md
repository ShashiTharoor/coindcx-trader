
### README.md

```markdown
# Crypto Manager for ELYINR

A comprehensive cryptocurrency trading and management system for ELYINR on CoinDCX with Discord notifications.

## Features

- **Price Tracking**: Real-time monitoring of ELYINR prices
- **Automated Trading**: Buy at 0.65 and sell at 0.7 automatically
- **Price Alerts**: Discord notifications when price thresholds are crossed
- **Trade Notifications**: Real-time updates on trades via Discord webhooks
- **Account Management**: Monitor your CoinDCX balance

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crypto-manager.git
   cd crypto-manager
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API credentials:
   ```
   COINDCX_API_KEY=your_api_key
   COINDCX_API_SECRET=your_api_secret
   DISCORD_WEBHOOK_URL=your_discord_webhook_url
   ```

## Usage

### Running the Full System

To run all components (price tracking, trading, and alerts):

```
python main.py --mode all
```

### Running Only the Trader

To run only the automated trading component:

```
python main.py --mode trader --buy-price 0.65 --sell-price 0.7
```

### Running Only Price Alerts

To run only the price alert system:

```
python main.py --mode alerts --high-alert 0.71 --low-alert 0.64
```

### Viewing Market Information

To display current market information and account balance:

```
python main.py --mode info
```

## Configuration

You can customize the system by editing the `config/settings.py` file:

- `TRADING_PAIR`: The cryptocurrency pair to trade (default: ELYINR)
- `BUY_PRICE`: The price at which to buy (default: 0.65)
- `SELL_PRICE`: The price at which to sell (default: 0.70)
- `PRICE_ALERT_THRESHOLDS`: Price thresholds for alerts
- `POLLING_INTERVAL`: How often to check prices (in seconds)

## Automated Trading Example

The system will automatically:

1. Monitor the ELYINR price continuously
2. Buy when the price drops to 0.65 or below
3. Sell when the price rises to 0.7 or above
4. Send Discord notifications for each action

## Running as a Background Service

To run the system as a background service on Linux, create a systemd service file:

```
[Unit]
Description=Crypto Manager Service
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/crypto-manager
ExecStart=/path/to/crypto-manager/venv/bin/python main.py --mode all
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Discord Notifications

The system sends the following notifications to your Discord channel:

- Price alerts when thresholds are crossed
- Trade notifications when orders are placed
- Trade confirmations when orders are filled
- System status updates

## Security

- API keys are stored in environment variables, not in the code
- HMAC authentication is used for secure API communication
- Retry logic with exponential backoff for API stability

## License

MIT
```

## Example code for the specific trading strategy (buy at 0.65, sell at 0.7)

Here's a simple script that you can use directly for the specific trading strategy you mentioned:

### buy_sell_strategy.py

```python
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
```

This project provides a comprehensive solution for managing your ELYINR cryptocurrency trading with automated buying at 0.65 and selling at 0.7, along with Discord notifications for price alerts and trade updates. The modular design allows you to extend the functionality as needed.
