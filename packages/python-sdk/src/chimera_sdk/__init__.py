"""Chimera Analytics Python SDK.

This package provides both synchronous and asynchronous clients for the
Chimera Multi-Agent Analytics System.

Example usage:

    Synchronous:
    >>> from chimera_sdk import ChimeraClient
    >>> client = ChimeraClient(api_url="https://api.example.com", api_key="key")
    >>> response = client.submit_query("What was the shielded transaction volume?")

    Asynchronous:
    >>> from chimera_sdk import AsyncChimeraClient
    >>> async with AsyncChimeraClient(api_url="https://api.example.com", api_key="key") as client:
    ...     response = await client.submit_query("What was the shielded transaction volume?")
"""

from .client import ChimeraClient
from .async_client import AsyncChimeraClient
from .exceptions import (
    ChimeraError,
    RateLimitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from .types import (
    ChimeraClientConfig,
    QueryRequest,
    QuerySubmissionResponse,
    QueryStatusResponse,
    QueryListResponse,
    Report,
    ReportSection,
    ReportListResponse,
    Dashboard,
    Widget,
    DashboardCreate,
    DashboardUpdate,
    DashboardListResponse,
    AlertRule,
    AlertCondition,
    NotificationChannel,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleListResponse,
    MetricsQuery,
    MetricsResponse,
    MetricDataPoint,
    Pagination,
    ErrorResponse,
    ExportFormat,
)

__version__ = "1.0.0"

__all__ = [
    # Clients
    "ChimeraClient",
    "AsyncChimeraClient",
    # Exceptions
    "ChimeraError",
    "RateLimitError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    # Types
    "ChimeraClientConfig",
    "QueryRequest",
    "QuerySubmissionResponse",
    "QueryStatusResponse",
    "QueryListResponse",
    "Report",
    "ReportSection",
    "ReportListResponse",
    "Dashboard",
    "Widget",
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardListResponse",
    "AlertRule",
    "AlertCondition",
    "NotificationChannel",
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRuleListResponse",
    "MetricsQuery",
    "MetricsResponse",
    "MetricDataPoint",
    "Pagination",
    "ErrorResponse",
    "ExportFormat",
]
