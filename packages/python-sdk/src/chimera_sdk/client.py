"""Synchronous Chimera client."""

from typing import Any, Dict, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .types import (
    ChimeraClientConfig,
    QueryRequest,
    QuerySubmissionResponse,
    QueryStatusResponse,
    QueryListResponse,
    Report,
    ReportListResponse,
    Dashboard,
    DashboardCreate,
    DashboardUpdate,
    DashboardListResponse,
    AlertRule,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleListResponse,
    MetricsQuery,
    MetricsResponse,
    ErrorResponse,
    ExportFormat,
)
from .exceptions import ChimeraError


class ChimeraClient:
    """Synchronous client for Chimera Analytics API."""

    def __init__(self, config: Union[ChimeraClientConfig, Dict[str, Any]]) -> None:
        """Initialize the client.

        Args:
            config: Client configuration as ChimeraClientConfig or dict
        """
        if isinstance(config, dict):
            config = ChimeraClientConfig(**config)

        self.config = config
        self.session = requests.Session()

        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({"Content-Type": "application/json"})
        if config.api_key:
            self.session.headers.update({"X-API-Key": config.api_key})

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Make an API request.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments for requests

        Returns:
            Response data

        Raises:
            ChimeraError: If the request fails
        """
        url = f"{self.config.api_url}{path}"
        timeout = kwargs.pop("timeout", self.config.timeout)

        try:
            response = self.session.request(
                method=method, url=url, params=params, json=json, timeout=timeout, **kwargs
            )
            response.raise_for_status()

            # Return None for 204 No Content
            if response.status_code == 204:
                return None

            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    raise ChimeraError(ErrorResponse(**error_data))
                except (ValueError, KeyError):
                    pass
            raise ChimeraError.from_http_error(e)
        except requests.exceptions.RequestException as e:
            raise ChimeraError.from_request_error(e)

    def health_check(self) -> Dict[str, str]:
        """Check API health status.

        Returns:
            Health status response
        """
        return self._request("GET", "/health")

    # Query Methods

    def submit_query(
        self, query: str, session_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> QuerySubmissionResponse:
        """Submit a natural language query.

        Args:
            query: Natural language query text
            session_id: Optional session ID for conversation context
            context: Optional additional context

        Returns:
            Query submission response
        """
        request = QueryRequest(query=query, session_id=session_id, context=context)
        data = self._request("POST", "/api/queries", json=request.__dict__)
        return QuerySubmissionResponse(**data)

    def get_query_status(self, query_id: str) -> QueryStatusResponse:
        """Get the status of a submitted query.

        Args:
            query_id: Query ID

        Returns:
            Query status response
        """
        data = self._request("GET", f"/api/queries/{query_id}")
        return QueryStatusResponse(**data)

    def list_queries(self, page: int = 1, limit: int = 20) -> QueryListResponse:
        """List user's query history.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Query list response
        """
        data = self._request("GET", "/api/queries", params={"page": page, "limit": limit})
        return QueryListResponse(**data)

    def cancel_query(self, query_id: str) -> Dict[str, str]:
        """Cancel a pending or processing query.

        Args:
            query_id: Query ID

        Returns:
            Cancellation response
        """
        return self._request("DELETE", f"/api/queries/{query_id}")

    # Report Methods

    def get_report(self, report_id: str) -> Report:
        """Retrieve a generated report.

        Args:
            report_id: Report ID

        Returns:
            Report data
        """
        data = self._request("GET", f"/api/reports/{report_id}")
        return Report(**data)

    def list_reports(
        self, page: int = 1, limit: int = 20, query_id: Optional[str] = None
    ) -> ReportListResponse:
        """List user's reports.

        Args:
            page: Page number
            limit: Items per page
            query_id: Optional filter by query ID

        Returns:
            Report list response
        """
        params = {"page": page, "limit": limit}
        if query_id:
            params["query_id"] = query_id
        data = self._request("GET", "/api/reports", params=params)
        return ReportListResponse(**data)

    def export_report(self, report_id: str, format: ExportFormat) -> Union[bytes, Report]:
        """Export a report in specified format.

        Args:
            report_id: Report ID
            format: Export format (pdf, html, json)

        Returns:
            Report data (bytes for pdf/html, Report object for json)
        """
        if format == "json":
            data = self._request("GET", f"/api/reports/{report_id}/export/{format}")
            return Report(**data)
        else:
            response = self.session.get(
                f"{self.config.api_url}/api/reports/{report_id}/export/{format}",
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.content

    # Dashboard Methods

    def create_dashboard(self, dashboard: Union[DashboardCreate, Dict[str, Any]]) -> Dashboard:
        """Create a new dashboard.

        Args:
            dashboard: Dashboard configuration

        Returns:
            Created dashboard
        """
        if isinstance(dashboard, DashboardCreate):
            dashboard = dashboard.__dict__
        data = self._request("POST", "/api/dashboards", json=dashboard)
        return Dashboard(**data)

    def get_dashboard(self, dashboard_id: str) -> Dashboard:
        """Retrieve a dashboard.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dashboard data
        """
        data = self._request("GET", f"/api/dashboards/{dashboard_id}")
        return Dashboard(**data)

    def update_dashboard(
        self, dashboard_id: str, updates: Union[DashboardUpdate, Dict[str, Any]]
    ) -> Dashboard:
        """Update a dashboard.

        Args:
            dashboard_id: Dashboard ID
            updates: Dashboard updates

        Returns:
            Updated dashboard
        """
        if isinstance(updates, DashboardUpdate):
            updates = updates.__dict__
        data = self._request("PUT", f"/api/dashboards/{dashboard_id}", json=updates)
        return Dashboard(**data)

    def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard.

        Args:
            dashboard_id: Dashboard ID
        """
        self._request("DELETE", f"/api/dashboards/{dashboard_id}")

    def list_dashboards(self, page: int = 1, limit: int = 20) -> DashboardListResponse:
        """List user's dashboards.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Dashboard list response
        """
        data = self._request("GET", "/api/dashboards", params={"page": page, "limit": limit})
        return DashboardListResponse(**data)

    # Alert Methods

    def create_alert_rule(self, rule: Union[AlertRuleCreate, Dict[str, Any]]) -> AlertRule:
        """Create a new alert rule.

        Args:
            rule: Alert rule configuration

        Returns:
            Created alert rule
        """
        if isinstance(rule, AlertRuleCreate):
            rule = rule.__dict__
        data = self._request("POST", "/api/alerts", json=rule)
        return AlertRule(**data)

    def get_alert_rule(self, rule_id: str) -> AlertRule:
        """Retrieve an alert rule.

        Args:
            rule_id: Alert rule ID

        Returns:
            Alert rule data
        """
        data = self._request("GET", f"/api/alerts/{rule_id}")
        return AlertRule(**data)

    def update_alert_rule(
        self, rule_id: str, updates: Union[AlertRuleUpdate, Dict[str, Any]]
    ) -> AlertRule:
        """Update an alert rule.

        Args:
            rule_id: Alert rule ID
            updates: Alert rule updates

        Returns:
            Updated alert rule
        """
        if isinstance(updates, AlertRuleUpdate):
            updates = updates.__dict__
        data = self._request("PUT", f"/api/alerts/{rule_id}", json=updates)
        return AlertRule(**data)

    def delete_alert_rule(self, rule_id: str) -> None:
        """Delete an alert rule.

        Args:
            rule_id: Alert rule ID
        """
        self._request("DELETE", f"/api/alerts/{rule_id}")

    def list_alert_rules(
        self, page: int = 1, limit: int = 20, enabled: Optional[bool] = None
    ) -> AlertRuleListResponse:
        """List user's alert rules.

        Args:
            page: Page number
            limit: Items per page
            enabled: Optional filter by enabled status

        Returns:
            Alert rule list response
        """
        params = {"page": page, "limit": limit}
        if enabled is not None:
            params["enabled"] = enabled
        data = self._request("GET", "/api/alerts", params=params)
        return AlertRuleListResponse(**data)

    # Metrics Methods

    def query_metrics(self, query: Union[MetricsQuery, Dict[str, Any]]) -> MetricsResponse:
        """Query time series metrics data.

        Args:
            query: Metrics query parameters

        Returns:
            Metrics data response
        """
        if isinstance(query, MetricsQuery):
            query = query.__dict__
        data = self._request("GET", "/api/metrics", params=query)
        return MetricsResponse(**data)
