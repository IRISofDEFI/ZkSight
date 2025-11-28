"""Type definitions for Chimera SDK."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union


@dataclass
class ChimeraClientConfig:
    """Configuration for Chimera client."""

    api_url: str
    api_key: Optional[str] = None
    timeout: int = 30


@dataclass
class QueryRequest:
    """Request to submit a query."""

    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class QuerySubmissionResponse:
    """Response from query submission."""

    query_id: str
    status: Literal["pending"]
    message: Optional[str] = None
    _links: Optional[Dict[str, str]] = None


@dataclass
class QueryResult:
    """Result of a query."""

    report_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QueryStatusResponse:
    """Response with query status."""

    query_id: str
    status: Literal["pending", "processing", "completed", "failed", "cancelled"]
    query: str
    result: Optional[QueryResult] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class QueryListItem:
    """Item in query list."""

    query_id: str
    query: str
    status: str
    created_at: str


@dataclass
class Pagination:
    """Pagination information."""

    page: int
    limit: int
    total: int
    pages: int


@dataclass
class QueryListResponse:
    """Response with list of queries."""

    queries: List[QueryListItem]
    pagination: Pagination


@dataclass
class ReportSection:
    """Section of a report."""

    title: str
    content: str
    order: int


@dataclass
class Report:
    """Generated report."""

    report_id: str
    query_id: str
    title: str
    executive_summary: str
    sections: List[ReportSection]
    visualizations: List[str]
    metadata: Dict[str, Any]
    created_at: str


@dataclass
class ReportListResponse:
    """Response with list of reports."""

    reports: List[Report]
    pagination: Pagination


@dataclass
class Widget:
    """Dashboard widget."""

    id: str
    type: Literal["chart", "metric", "alert_list", "report"]
    position: Dict[str, int]
    config: Dict[str, Any]


@dataclass
class Dashboard:
    """Dashboard configuration."""

    id: str
    name: str
    layout: Dict[str, Any]
    widgets: List[Widget]
    refresh_interval: int
    shared: bool
    created_at: str
    updated_at: str
    description: Optional[str] = None


@dataclass
class DashboardCreate:
    """Request to create a dashboard."""

    name: str
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Widget]] = None
    refresh_interval: Optional[int] = None


@dataclass
class DashboardUpdate:
    """Request to update a dashboard."""

    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    widgets: Optional[List[Widget]] = None
    refresh_interval: Optional[int] = None


@dataclass
class DashboardListResponse:
    """Response with list of dashboards."""

    dashboards: List[Dashboard]
    pagination: Pagination


@dataclass
class AlertCondition:
    """Condition for alert rule."""

    metric: str
    operator: Literal[">", "<", "==", "!=", "change_pct"]
    threshold: float
    duration: Optional[int] = None
    cooldown: Optional[int] = None


@dataclass
class NotificationChannel:
    """Notification channel configuration."""

    type: Literal["email", "webhook", "websocket", "sms"]
    config: Dict[str, Any]


@dataclass
class AlertRule:
    """Alert rule configuration."""

    id: str
    name: str
    condition: AlertCondition
    channels: List[NotificationChannel]
    enabled: bool
    created_at: str
    updated_at: str
    description: Optional[str] = None


@dataclass
class AlertRuleCreate:
    """Request to create an alert rule."""

    name: str
    condition: AlertCondition
    description: Optional[str] = None
    channels: Optional[List[NotificationChannel]] = None
    enabled: Optional[bool] = True


@dataclass
class AlertRuleUpdate:
    """Request to update an alert rule."""

    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[AlertCondition] = None
    channels: Optional[List[NotificationChannel]] = None
    enabled: Optional[bool] = None


@dataclass
class AlertRuleListResponse:
    """Response with list of alert rules."""

    rules: List[AlertRule]
    pagination: Pagination


@dataclass
class MetricsQuery:
    """Query for metrics data."""

    metric: str
    start: str
    end: Optional[str] = None
    aggregation: Optional[Literal["mean", "sum", "min", "max", "count"]] = None
    interval: Optional[str] = None


@dataclass
class MetricDataPoint:
    """Single metric data point."""

    timestamp: str
    value: float
    tags: Optional[Dict[str, str]] = None


@dataclass
class MetricsResponse:
    """Response with metrics data."""

    metric: str
    time_range: Dict[str, Any]
    data: List[MetricDataPoint]
    count: int
    aggregation: Optional[str] = None
    interval: Optional[str] = None


@dataclass
class ErrorDetail:
    """Error details."""

    code: str
    message: str
    retryable: bool
    details: Optional[Dict[str, Any]] = None


@dataclass
class ErrorResponse:
    """Error response from API."""

    error: ErrorDetail
    request_id: str
    timestamp: int


ExportFormat = Literal["pdf", "html", "json"]
