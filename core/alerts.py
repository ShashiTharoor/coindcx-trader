import time
from typing import Dict, Any, Optional, List
from threading import Thread

from config.settings import PRICE_ALERT_THRESHOLDS, TRADING_PAIR, POLLING_INTERVAL
from config.logging_config import logger
from api.coindcx import CoinDCXAPI
from api.discord import DiscordWebhook
from core.tracker import PriceTracker

class AlertSystem:
    def __init__(self, trading_pair: Optional[str] = None, 
                 thresholds: Optional[Dict[str, float]] = None,
                 tracker: Optional[PriceTracker] = None):
        self.trading_pair = trading_pair or TRADING_PAIR
        self.thresholds = thresholds or PRICE_ALERT_THRESHOLDS
        self.discord = DiscordWebhook()
        self.tracker = tracker or PriceTracker(self.trading_pair)
        self.triggered_alerts = set()  # Keep track of already triggered alerts
        self._running = False
        self._alert_thread = None
    
    def add_threshold(self, alert_type: str, price: float) -> None:
        """Add a new price threshold alert."""
        self.thresholds[alert_type] = price
        logger.info(f"Added {alert_type} alert threshold at {price}")
    
    def remove_threshold(self, alert_type: str) -> None:
        """Remove a price threshold alert."""
        if alert_type in self.thresholds:
            del self.thresholds[alert_type]
            logger.info(f"Removed {alert_type} alert threshold")
    
    def check_alerts(self, current_price: float) -> List[Dict[str, Any]]:
        """Check if any alerts should be triggered based on current price."""
        triggered = []
        
        for alert_type, threshold in self.thresholds.items():
            alert_id = f"{alert_type}_{threshold}"
            
            if alert_type.lower() == "high" and current_price >= threshold:
                if alert_id not in self.triggered_alerts:
                    triggered.append({
                        "type": alert_type,
                        "threshold": threshold,
                        "current_price": current_price
                    })
                    self.triggered_alerts.add(alert_id)
            
            elif alert_type.lower() == "low" and current_price <= threshold:
                if alert_id not in self.triggered_alerts:
                    triggered.append({
                        "type": alert_type,
                        "threshold": threshold,
                        "current_price": current_price
                    })
                    self.triggered_alerts.add(alert_id)
            
            # Reset triggered alert if price moves back beyond threshold
            elif (alert_type.lower() == "high" and current_price < threshold * 0.98) or \
                 (alert_type.lower() == "low" and current_price > threshold * 1.02):
                if alert_id in self.triggered_alerts:
                    self.triggered_alerts.remove(alert_id)
        
        return triggered
    
    def price_callback(self, price: float) -> None:
        """Callback function for price tracker."""
        alerts = self.check_alerts(price)
        
        for alert in alerts:
            logger.info(f"Price alert triggered: {alert['type']} at {alert['current_price']}")
            self.discord.send_price_alert(
                self.trading_pair,
                alert["current_price"],
                alert["type"],
                alert["threshold"]
            )
    
    def start_monitoring(self, use_existing_tracker: bool = False) -> None:
        """Start monitoring for price alerts."""
        if self._running:
            logger.warning("Alert monitoring is already running")
            return
        
        self._running = True
        
        if use_existing_tracker:
            # Register callback with existing tracker
            self.tracker.register_callback(self.price_callback)
            logger.info(f"Alert monitoring started for {self.trading_pair} using existing tracker")
        else:
            # Start a new thread for monitoring
            def monitor_loop():
                logger.info(f"Alert monitoring started for {self.trading_pair}")
                try:
                    while self._running:
                        current_price = self.tracker.get_current_price()
                        self.price_callback(current_price)
                        time.sleep(POLLING_INTERVAL)
                except Exception as e:
                    logger.error(f"Error in alert monitoring: {str(e)}")
                finally:
                    logger.info("Alert monitoring stopped")
            
            self._alert_thread = Thread(target=monitor_loop, daemon=True)
            self._alert_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring for price alerts."""
        self._running = False
        logger.info("Stopping alert monitoring")