"""Dashboard configuration models for MongoDB"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LayoutConfig(BaseModel):
    """Dashboard layout configuration"""
    columns: int = 12
    row_height: int = 100
    breakpoints: Optional[Dict[str, int]] = None


class WidgetPosition(BaseModel):
    """Widget position in grid"""
    x: int
    y: int
    w: int
    h: int


class WidgetConfig(BaseModel):
    """Widget configuration"""
    metric: Optional[str] = None
    time_range: Optional[Dict[str, str]] = None
    chart_type: Optional[str] = None
    aggregation: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    display_options: Optional[Dict[str, Any]] = None


class Widget(BaseModel):
    """Dashboard widget"""
    id: str
    type: str
    position: WidgetPosition
    config: WidgetConfig
    title: Optional[str] = None
    description: Optional[str] = None


class Dashboard(BaseModel):
    """Dashboard document"""
    dashboard_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    widgets: List[Widget] = Field(default_factory=list)
    refresh_interval: int = 60
    shared: bool = False
    shared_with: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection name
DASHBOARD_COLLECTION = "dashboards"

# Index specifications
DASHBOARD_INDEXES = [
    {"keys": [("dashboard_id", 1)], "unique": True, "name": "idx_dashboardId"},
    {"keys": [("user_id", 1)], "name": "idx_userId"},
    {"keys": [("user_id", 1), ("created_at", -1)], "name": "idx_userId_createdAt"},
    {"keys": [("shared", 1)], "name": "idx_shared"},
    {"keys": [("tags", 1)], "name": "idx_tags"},
]
