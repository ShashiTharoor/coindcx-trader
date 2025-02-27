import time
import signal
import sys
from typing import Optional, Dict, List

from config.settings import TRADING_PAIR, PRICE_ALERT_THRESHOLDS
from config.logging_config import logger
from core.alerts import AlertSystem
from core.tracker import PriceTracker

def run_price_alerts(trading_pair: Optional[str] = None, 
                    thresholds: Optional[Dict[str, float]] = None) -> None:
    """Run the price alert system."""
    pair = trading_pair or TRADING_PAIR
    alert_thresholds = thresholds or PRICE_ALERT_THRESHOLDS
    
    logger.info(f"Starting price alerts for {pair}")
    logger.info(f"Alert thresholds: {alert_thresholds}")
    
    # Create tracker and alert system
    tracker = PriceTracker(pair)
    alert_system = AlertSystem(pair, alert_thresholds, tracker)
    
    # Start alert monitoring
    alert_system.start_monitoring(use_existing_tracker=False)
    
    # Register signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        alert_system.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        alert_system.stop_monitoring()

# Run price alerts if script is executed directly
if __name__ == "__main__":
    run_price_alerts()