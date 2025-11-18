"""Notification delivery system."""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from .alert_engine import Alert

logger = logging.getLogger(__name__)


@dataclass
class NotificationChannel:
    """Notification channel configuration."""

    type: str  # email, webhook, websocket, sms
    config: Dict[str, Any]


class NotificationDispatcher:
    """Dispatches notifications to various channels."""

    def __init__(self):
        """Initialize notification dispatcher."""
        self.channels: Dict[str, NotificationChannel] = {}

    def register_channel(
        self, channel_id: str, channel: NotificationChannel
    ) -> None:
        """
        Register notification channel.

        Args:
            channel_id: Channel identifier
            channel: Channel configuration
        """
        self.channels[channel_id] = channel
        logger.info(f"Registered notification channel: {channel_id} ({channel.type})")

    async def send_alert(self, alert: Alert, channels: List[str]) -> None:
        """
        Send alert to specified channels.

        Args:
            alert: Alert to send
            channels: List of channel IDs
        """
        for channel_id in channels:
            if channel_id not in self.channels:
                logger.warning(f"Channel not found: {channel_id}")
                continue

            channel = self.channels[channel_id]
            try:
                if channel.type == "email":
                    await self._send_email(alert, channel.config)
                elif channel.type == "webhook":
                    await self._send_webhook(alert, channel.config)
                elif channel.type == "websocket":
                    await self._send_websocket(alert, channel.config)
                elif channel.type == "sms":
                    await self._send_sms(alert, channel.config)
                else:
                    logger.warning(f"Unknown channel type: {channel.type}")
            except Exception as e:
                logger.error(f"Error sending alert via {channel_id}: {e}", exc_info=True)

    async def _send_email(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send email notification."""
        # Placeholder - would use SendGrid/SMTP
        logger.info(f"Would send email alert: {alert.rule_id}")

    async def _send_webhook(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send webhook notification."""
        import httpx

        url = config.get("url")
        if not url:
            logger.warning("Webhook URL not configured")
            return

        payload = {
            "rule_id": alert.rule_id,
            "metric": alert.metric,
            "value": alert.current_value,
            "threshold": alert.threshold,
            "severity": alert.severity,
            "timestamp": alert.timestamp,
        }

        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)

        logger.info(f"Sent webhook alert: {alert.rule_id}")

    async def _send_websocket(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send WebSocket notification."""
        # Placeholder - would use Socket.io or similar
        logger.info(f"Would send WebSocket alert: {alert.rule_id}")

    async def _send_sms(self, alert: Alert, config: Dict[str, Any]) -> None:
        """Send SMS notification."""
        # Placeholder - would use Twilio
        logger.info(f"Would send SMS alert: {alert.rule_id}")

