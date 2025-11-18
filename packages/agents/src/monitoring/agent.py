"""Monitoring Agent implementation."""
import logging
from typing import Dict, Type, Any, Optional
import redis
from ..messaging import BaseAgent, ConnectionPool, create_metadata
from ..config import AgentConfig
from .scheduler import MonitoringScheduler
from .alert_engine import AlertEngine, AlertRule
from .notifier import NotificationDispatcher
from .state_manager import MonitoringStateManager

logger = logging.getLogger(__name__)

try:
    from ..messaging.generated import messages_pb2

    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False

    class messages_pb2:
        class AlertRule:
            pass

        class MonitoringEvent:
            pass


class MonitoringAgent(BaseAgent):
    """Monitors metrics and triggers alerts."""

    AGENT_NAME = "monitoring_agent"
    EXCHANGE_NAME = "chimera.events"

    ROUTING_KEY_ALERT = "monitoring.alert"
    ROUTING_KEY_RULE_CONFIG = "monitoring.rule.config"

    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        redis_client: Optional[redis.Redis] = None,
    ):
        """
        Initialize Monitoring Agent.

        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            redis_client: Optional Redis client
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[self.ROUTING_KEY_RULE_CONFIG],
        )

        self.config = config

        if redis_client is None:
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
            )

        self.scheduler = MonitoringScheduler()
        self.alert_engine = AlertEngine()
        self.notifier = NotificationDispatcher()
        self.state_manager = MonitoringStateManager(redis_client)

        # Load rules from state
        self._load_rules_from_state()

        # Set up polling jobs
        self._setup_polling_jobs()

        logger.info(f"{self.AGENT_NAME} initialized")

    def _load_rules_from_state(self) -> None:
        """Load alert rules from Redis state."""
        rules = self.state_manager.load_all_rules()
        for rule in rules.values():
            self.alert_engine.add_rule(rule)
        logger.info(f"Loaded {len(rules)} alert rules from state")

    def _setup_polling_jobs(self) -> None:
        """Set up periodic polling jobs."""
        # Poll network metrics every 5 minutes
        self.scheduler.add_polling_job(
            "poll_network",
            self._poll_network_metrics,
            interval_seconds=300,
        )

        # Poll market data every 1 minute
        self.scheduler.add_polling_job(
            "poll_market",
            self._poll_market_data,
            interval_seconds=60,
        )

        # Poll social data every 15 minutes
        self.scheduler.add_polling_job(
            "poll_social",
            self._poll_social_data,
            interval_seconds=900,
        )

    def start(self) -> None:
        """Start monitoring agent."""
        self.scheduler.start()
        logger.info("Monitoring agent started")

    def stop(self) -> None:
        """Stop monitoring agent."""
        self.scheduler.stop()
        logger.info("Monitoring agent stopped")

    def get_routing_key_map(self) -> Dict[str, Type]:
        """Get routing key to message class mapping."""
        if not PROTO_AVAILABLE:
            return {}
        return {
            self.ROUTING_KEY_RULE_CONFIG: messages_pb2.AlertRule,
        }

    def route_message(
        self, message: Any, routing_key: str, properties: Dict[str, Any]
    ) -> None:
        """Route message to appropriate handler."""
        if routing_key == self.ROUTING_KEY_RULE_CONFIG:
            self._handle_rule_config(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_rule_config(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle alert rule configuration change."""
        try:
            # Parse rule from message
            rule = self._parse_rule_from_message(message)
            if rule:
                self.alert_engine.add_rule(rule)
                self.state_manager.save_rule(rule)
                logger.info(f"Updated alert rule: {rule.id}")
        except Exception as e:
            logger.error(f"Error handling rule config: {e}", exc_info=True)

    def _parse_rule_from_message(self, message: Any) -> Optional[AlertRule]:
        """Parse alert rule from message."""
        from .alert_engine import AlertCondition

        try:
            rule_id = getattr(message, "id", "")
            name = getattr(message, "name", "")
            condition = getattr(message, "condition", None)

            if not condition:
                return None

            alert_condition = AlertCondition(
                metric=getattr(condition, "metric", ""),
                operator=getattr(condition, "operator", ">"),
                threshold=getattr(condition, "threshold", 0.0),
                duration_seconds=getattr(condition, "duration_seconds", 0),
                cooldown_seconds=getattr(condition, "cooldown_seconds", 300),
            )

            channels = list(getattr(message, "notification_channels", []))
            enabled = getattr(message, "enabled", True)

            return AlertRule(
                id=rule_id,
                name=name,
                condition=alert_condition,
                notification_channels=channels,
                enabled=enabled,
            )
        except Exception as e:
            logger.error(f"Error parsing rule: {e}")
            return None

    async def _poll_network_metrics(self) -> None:
        """Poll network metrics."""
        # Placeholder - would query blockchain node
        logger.debug("Polling network metrics")

    async def _poll_market_data(self) -> None:
        """Poll market data."""
        # Placeholder - would query exchange APIs
        logger.debug("Polling market data")

    async def _poll_social_data(self) -> None:
        """Poll social data."""
        # Placeholder - would query social APIs
        logger.debug("Polling social data")

    def evaluate_metric(self, metric: str, value: float) -> None:
        """
        Evaluate metric value and trigger alerts if needed.

        Args:
            metric: Metric name
            value: Current value
        """
        alerts = self.alert_engine.evaluate(metric, value)

        for alert in alerts:
            # Get rule to find notification channels
            rule = self.alert_engine.rules.get(alert.rule_id)
            if rule:
                import asyncio

                asyncio.run(
                    self.notifier.send_alert(alert, rule.notification_channels)
                )

            # Publish alert event
            self._publish_alert(alert)

    def _publish_alert(self, alert: Alert) -> None:
        """Publish alert event."""
        if not PROTO_AVAILABLE:
            logger.info(f"Would publish alert: {alert.rule_id}")
            return

        event = messages_pb2.MonitoringEvent()
        event.metadata.CopyFrom(create_metadata(self.AGENT_NAME))
        event.alert.rule_id = alert.rule_id
        event.alert.timestamp = alert.timestamp
        event.alert.metric = alert.metric
        event.alert.current_value = alert.current_value
        event.alert.threshold = alert.threshold
        event.alert.severity = alert.severity

        self.publish_event(
            message=event,
            routing_key=self.ROUTING_KEY_ALERT,
        )

        logger.info(f"Published alert: {alert.rule_id}")

