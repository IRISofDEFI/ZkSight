"""User profile models for MongoDB"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NotificationSettings(BaseModel):
    """Notification preferences"""
    email: bool = True
    webhook: bool = False
    in_app: bool = True
    sms: bool = False


class TimeRange(BaseModel):
    """Time range specification"""
    start: str
    end: str


class UserPreferences(BaseModel):
    """User preferences"""
    default_time_range: TimeRange = Field(
        default_factory=lambda: TimeRange(start="-7d", end="now")
    )
    favorite_metrics: List[str] = Field(default_factory=list)
    notification_settings: NotificationSettings = Field(
        default_factory=NotificationSettings
    )


class ApiKey(BaseModel):
    """API key configuration"""
    id: str
    name: str
    key: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class UserProfile(BaseModel):
    """User profile document"""
    user_id: str
    email: str
    password_hash: Optional[str] = None
    expertise_level: str = "intermediate"
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    dashboard_ids: List[str] = Field(default_factory=list)
    api_keys: List[ApiKey] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection name
USER_COLLECTION = "users"

# Index specifications
USER_INDEXES = [
    {"keys": [("user_id", 1)], "unique": True, "name": "idx_userId"},
    {"keys": [("email", 1)], "unique": True, "name": "idx_email"},
    {"keys": [("api_keys.key", 1)], "sparse": True, "name": "idx_apiKey"},
    {"keys": [("created_at", 1)], "name": "idx_createdAt"},
]
