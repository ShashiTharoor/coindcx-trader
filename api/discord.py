import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.settings import DISCORD_WEBHOOK_URL
from config.logging_config import logger

class DiscordWebhook:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        
        if not self.webhook_url:
            raise ValueError("Discord webhook URL not found. Please check your environment variables.")
    
    def send_message(self, content: str) -> bool:
        """Send a simple text message to Discord."""
        payload = {
            "content": content
        }
        
        return self._send_payload(payload)
    
    def send_embed(self, title: str, description: str, color: int = 0x00ff00, 
                   fields: Optional[List[Dict[str, Any]]] = None, 
                   thumbnail: Optional[str] = None,
                   footer: Optional[str] = None) -> bool:
        """Send an embedded message to Discord."""
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if fields:
            embed["fields"] = fields
        
        if thumbnail:
            embed["thumbnail"] = {"url": thumbnail}
        
        if footer:
            embed["footer"] = {"text": footer}
        
        payload = {
            "embeds": [embed]
        }
        
        return self._send_payload(payload)
    
    def send_price_alert(self, market: str, price: float, alert_type: str, 
                         threshold: float) -> bool:
        """Send a price alert embed."""
        # Set color based on alert type
        color = 0x00ff00 if alert_type.lower() == "high" else 0xff0000
        
        title = f"🚨 PRICE ALERT: {market}"
        description = f"**Current Price**: {price}\n**Threshold**: {threshold}"
        
        fields = [
            {
                "name": "Alert Type",
                "value": f"{'⬆️ Price Above Threshold' if alert_type.lower() == 'high' else '⬇️ Price Below Threshold'}",
                "inline": True
            },
            {
                "name": "Time",
                "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "inline": True
            }
        ]
        
        return self.send_embed(title, description, color, fields, 
                              thumbnail="https://cryptologos.cc/logos/elrond-egld-egld-logo.png",
                              footer="Crypto Manager Alert System")
    
    def send_trade_notification(self, trade_type: str, market: str, price: float, 
                               quantity: float, total: float, order_id: str) -> bool:
        """Send a trade notification embed."""
        # Set color based on trade type
        color = 0x00ff00 if trade_type.lower() == "buy" else 0xff0000
        
        title = f"{'🟢 BUY ORDER' if trade_type.lower() == 'buy' else '🔴 SELL ORDER'}: {market}"
        description = f"**Price**: {price}\n**Quantity**: {quantity}\n**Total**: {total}"
        
        fields = [
            {
                "name": "Order ID",
                "value": order_id,
                "inline": False
            },
            {
                "name": "Time",
                "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "inline": True
            }
        ]
        
        return self.send_embed(title, description, color, fields,
                              thumbnail="https://cryptologos.cc/logos/elrond-egld-egld-logo.png",
                              footer="Crypto Manager Trading System")
    
    def _send_payload(self, payload: Dict[str, Any]) -> bool:
        """Send payload to Discord webhook."""
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Discord notification sent successfully: {payload.get('content') or 'Embed'}")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return False