"""Alert rule engine."""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AlertCondition:
    """Alert condition model."""

    metric: str
    operator: str  # >, <, >=, <=, ==
    threshold: float
    duration_seconds: int
    cooldown_seconds: int


@dataclass
class AlertRule:
    """Alert rule model."""

    id: str
    name: str
    condition: AlertCondition
    notification_channels: List[str]
    enabled: bool


@dataclass
class Alert:
    """Alert model."""

    rule_id: str
    timestamp: int
    metric: str
    current_value: float
    threshold: float
    severity: str
    context: Dict[str, str]
    suggested_actions: List[str]


class AlertEngine:
    """Evaluates alert conditions and generates alerts."""

    def __init__(self):
        """Initialize alert engine."""
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: Dict[str, List[Alert]] = {}
        self.last_alert_time: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add alert rule.

        Args:
            rule: Alert rule
        """
        self.rules[rule.id] = rule
        self.alert_history[rule.id] = []
        logger.info(f"Added alert rule: {rule.id} ({rule.name})")

    def remove_rule(self, rule_id: str) -> None:
        """
        Remove alert rule.

        Args:
            rule_id: Rule identifier
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            if rule_id in self.alert_history:
                del self.alert_history[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def evaluate(
        self, metric: str, value: float, timestamp: Optional[int] = None
    ) -> List[Alert]:
        """
        Evaluate metric value against alert rules.

        Args:
            metric: Metric name
            value: Current metric value
            timestamp: Optional timestamp

        Returns:
            List of triggered alerts
        """
        alerts = []
        current_time = datetime.now()

        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            if rule.condition.metric != metric:
                continue

            # Check condition
            condition_met = self._check_condition(
                value, rule.condition.operator, rule.condition.threshold
            )

            if condition_met:
                # Check cooldown
                last_alert = self.last_alert_time.get(rule_id)
                if last_alert:
                    cooldown = timedelta(seconds=rule.condition.cooldown_seconds)
                    if current_time - last_alert < cooldown:
                        continue  # Still in cooldown

                # Check duration (simplified - would track state over time)
                # For now, trigger immediately if condition met

                alert = Alert(
                    rule_id=rule_id,
                    timestamp=int((timestamp or current_time.timestamp()) * 1000),
                    metric=metric,
                    current_value=value,
                    threshold=rule.condition.threshold,
                    severity=self._calculate_severity(value, rule.condition),
                    context={"rule_name": rule.name},
                    suggested_actions=self._suggest_actions(metric, value),
                )

                alerts.append(alert)
                self.alert_history[rule_id].append(alert)
                self.last_alert_time[rule_id] = current_time

                logger.warning(
                    f"Alert triggered: {rule.name} - {metric}={value} "
                    f"(threshold={rule.condition.threshold})"
                )

        return alerts

    def _check_condition(
        self, value: float, operator: str, threshold: float
    ) -> bool:
        """Check if condition is met."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.01
        return False

    def _calculate_severity(
        self, value: float, condition: AlertCondition
    ) -> str:
        """Calculate alert severity."""
        deviation = abs(value - condition.threshold) / condition.threshold if condition.threshold > 0 else 0

        if deviation > 0.5:
            return "critical"
        elif deviation > 0.2:
            return "high"
        elif deviation > 0.1:
            return "medium"
        else:
            return "low"

    def _suggest_actions(self, metric: str, value: float) -> List[str]:
        """Suggest actions based on metric and value."""
        suggestions = [
            f"Review {metric} data for anomalies",
            "Check related metrics for correlation",
        ]
        return suggestions

    def get_alert_history(self, rule_id: str, limit: int = 10) -> List[Alert]:
        """
        Get alert history for a rule.

        Args:
            rule_id: Rule identifier
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        return self.alert_history.get(rule_id, [])[-limit:]

