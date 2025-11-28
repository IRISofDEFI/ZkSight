"""Alert rule models for MongoDB"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AlertCondition(BaseModel):
    """Alert condition specification"""
    metric: str
    operator: str
    threshold: float
    duration: Optional[int] = None
    cooldown: Optional[int] = None


class WebhookConfig(BaseModel):
    """Webhook notification configuration"""
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


class EmailConfig(BaseModel):
    """Email notification configuration"""
    to: List[str]
    cc: Optional[List[str]] = None
    subject: Optional[str] = None
    template: Optional[str] = None


class SmsConfig(BaseModel):
    """SMS notification configuration"""
    phone_numbers: List[str]
    message: Optional[str] = None


class NotificationChannelConfig(BaseModel):
    """Notification channel configuration"""
    type: str
    enabled: bool = True
    webhook: Optional[WebhookConfig] = None
    email: Optional[EmailConfig] = None
    sms: Optional[SmsConfig] = None


class AlertRule(BaseModel):
    """Alert rule document"""
    alert_rule_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    condition: AlertCondition
    channels: List[NotificationChannelConfig]
    enabled: bool = True
    tags: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertHistory(BaseModel):
    """Alert history document"""
    alert_history_id: str
    alert_rule_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric: str
    current_value: float
    threshold: float
    severity: str
    context: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions: Optional[List[str]] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection names
ALERT_RULE_COLLECTION = "alert_rules"
ALERT_HISTORY_COLLECTION = "alert_history"

# Index specifications
ALERT_RULE_INDEXES = [
    {"keys": [("alert_rule_id", 1)], "unique": True, "name": "idx_alertRuleId"},
    {"keys": [("user_id", 1)], "name": "idx_userId"},
    {"keys": [("user_id", 1), ("enabled", 1)], "name": "idx_userId_enabled"},
    {"keys": [("condition.metric", 1)], "name": "idx_metric"},
    {"keys": [("tags", 1)], "name": "idx_tags"},
]

ALERT_HISTORY_INDEXES = [
    {"keys": [("alert_history_id", 1)], "unique": True, "name": "idx_alertHistoryId"},
    {"keys": [("alert_rule_id", 1)], "name": "idx_alertRuleId"},
    {"keys": [("user_id", 1)], "name": "idx_userId"},
    {"keys": [("user_id", 1), ("timestamp", -1)], "name": "idx_userId_timestamp"},
    {"keys": [("timestamp", -1)], "name": "idx_timestamp"},
    {"keys": [("acknowledged", 1)], "name": "idx_acknowledged"},
]
