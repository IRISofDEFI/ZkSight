"""Monitoring state persistence."""
import logging
import json
from typing import Dict, Any, Optional
import redis
from ..config import AgentConfig
from .alert_engine import AlertRule

logger = logging.getLogger(__name__)


class MonitoringStateManager:
    """Manages monitoring state in Redis."""

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize state manager.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def save_rule(self, rule: AlertRule) -> None:
        """
        Save alert rule to Redis.

        Args:
            rule: Alert rule
        """
        key = f"monitoring:rule:{rule.id}"
        data = {
            "id": rule.id,
            "name": rule.name,
            "condition": {
                "metric": rule.condition.metric,
                "operator": rule.condition.operator,
                "threshold": rule.condition.threshold,
                "duration_seconds": rule.condition.duration_seconds,
                "cooldown_seconds": rule.condition.cooldown_seconds,
            },
            "notification_channels": rule.notification_channels,
            "enabled": rule.enabled,
        }
        self.redis.set(key, json.dumps(data))
        logger.info(f"Saved alert rule: {rule.id}")

    def load_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        Load alert rule from Redis.

        Args:
            rule_id: Rule identifier

        Returns:
            Alert rule or None
        """
        key = f"monitoring:rule:{rule_id}"
        data = self.redis.get(key)
        if not data:
            return None

        try:
            rule_dict = json.loads(data)
            from .alert_engine import AlertCondition

            condition = AlertCondition(
                metric=rule_dict["condition"]["metric"],
                operator=rule_dict["condition"]["operator"],
                threshold=rule_dict["condition"]["threshold"],
                duration_seconds=rule_dict["condition"]["duration_seconds"],
                cooldown_seconds=rule_dict["condition"]["cooldown_seconds"],
            )

            return AlertRule(
                id=rule_dict["id"],
                name=rule_dict["name"],
                condition=condition,
                notification_channels=rule_dict["notification_channels"],
                enabled=rule_dict["enabled"],
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading rule {rule_id}: {e}")
            return None

    def load_all_rules(self) -> Dict[str, AlertRule]:
        """
        Load all alert rules.

        Returns:
            Dictionary of rule ID to AlertRule
        """
        rules = {}
        pattern = "monitoring:rule:*"
        for key in self.redis.scan_iter(match=pattern):
            rule_id = key.decode().split(":")[-1]
            rule = self.load_rule(rule_id)
            if rule:
                rules[rule_id] = rule
        return rules

    def delete_rule(self, rule_id: str) -> None:
        """
        Delete alert rule from Redis.

        Args:
            rule_id: Rule identifier
        """
        key = f"monitoring:rule:{rule_id}"
        self.redis.delete(key)
        logger.info(f"Deleted alert rule: {rule_id}")

