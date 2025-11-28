"""Asynchronous Chimera client."""

from typing import Any, Dict, Optional, Union
import aiohttp

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


class AsyncChimeraClient:
    """Asynchronous client for Chimera Analytics API."""

    def __init__(self, config: Union[ChimeraClientConfig, Dict[str, Any]]) -> None:
        """Initialize the async client.

        Args:
            config: Client configuration as ChimeraClientConfig or dict
        """
        if isinstance(config, dict):
            config = ChimeraClientConfig(**config)

        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AsyncChimeraClient":
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure session is created."""
        if self._session is None or self._session.closed:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["X-API-Key"] = self.config.api_key

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
            )

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Make an async API request.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments

        Returns:
            Response data

        Raises:
            ChimeraError: If the request fails
        """
        await self._ensure_session()
        url = f"{self.config.api_url}{path}"

        try:
            async with self._session.request(  # type: ignore
                method=method, url=url, params=params, json=json, **kwargs
            ) as response:
                # Return None for 204 No Content
                if response.status == 204:
                    return None

                data = await response.json()

                if response.status >= 400:
                    raise ChimeraError(ErrorResponse(**data))

                return data
        except aiohttp.ClientError as e:
            raise ChimeraError.from_request_error(e)

    async def health_check(self) -> Dict[str, str]:
        """Check API health status.

        Returns:
            Health status response
        """
        return await self._request("GET", "/health")

    # Query Methods

    async def submit_query(
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
        data = await self._request("POST", "/api/queries", json=request.__dict__)
        return QuerySubmissionResponse(**data)

    async def get_query_status(self, query_id: str) -> QueryStatusResponse:
        """Get the status of a submitted query.

        Args:
            query_id: Query ID

        Returns:
            Query status response
        """
        data = await self._request("GET", f"/api/queries/{query_id}")
        return QueryStatusResponse(**data)

    async def list_queries(self, page: int = 1, limit: int = 20) -> QueryListResponse:
        """List user's query history.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Query list response
        """
        data = await self._request("GET", "/api/queries", params={"page": page, "limit": limit})
        return QueryListResponse(**data)

    async def cancel_query(self, query_id: str) -> Dict[str, str]:
        """Cancel a pending or processing query.

        Args:
            query_id: Query ID

        Returns:
            Cancellation response
        """
        return await self._request("DELETE", f"/api/queries/{query_id}")

    # Report Methods

    async def get_report(self, report_id: str) -> Report:
        """Retrieve a generated report.

        Args:
            report_id: Report ID

        Returns:
            Report data
        """
        data = await self._request("GET", f"/api/reports/{report_id}")
        return Report(**data)

    async def list_reports(
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
        data = await self._request("GET", "/api/reports", params=params)
        return ReportListResponse(**data)

    async def export_report(self, report_id: str, format: ExportFormat) -> Union[bytes, Report]:
        """Export a report in specified format.

        Args:
            report_id: Report ID
            format: Export format (pdf, html, json)

        Returns:
            Report data (bytes for pdf/html, Report object for json)
        """
        if format == "json":
            data = await self._request("GET", f"/api/reports/{report_id}/export/{format}")
            return Report(**data)
        else:
            await self._ensure_session()
            url = f"{self.config.api_url}/api/reports/{report_id}/export/{format}"
            async with self._session.get(url) as response:  # type: ignore
                response.raise_for_status()
                return await response.read()

    # Dashboard Methods

    async def create_dashboard(
        self, dashboard: Union[DashboardCreate, Dict[str, Any]]
    ) -> Dashboard:
        """Create a new dashboard.

        Args:
            dashboard: Dashboard configuration

        Returns:
            Created dashboard
        """
        if isinstance(dashboard, DashboardCreate):
            dashboard = dashboard.__dict__
        data = await self._request("POST", "/api/dashboards", json=dashboard)
        return Dashboard(**data)

    async def get_dashboard(self, dashboard_id: str) -> Dashboard:
        """Retrieve a dashboard.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dashboard data
        """
        data = await self._request("GET", f"/api/dashboards/{dashboard_id}")
        return Dashboard(**data)

    async def update_dashboard(
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
        data = await self._request("PUT", f"/api/dashboards/{dashboard_id}", json=updates)
        return Dashboard(**data)

    async def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard.

        Args:
            dashboard_id: Dashboard ID
        """
        await self._request("DELETE", f"/api/dashboards/{dashboard_id}")

    async def list_dashboards(self, page: int = 1, limit: int = 20) -> DashboardListResponse:
        """List user's dashboards.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Dashboard list response
        """
        data = await self._request("GET", "/api/dashboards", params={"page": page, "limit": limit})
        return DashboardListResponse(**data)

    # Alert Methods

    async def create_alert_rule(self, rule: Union[AlertRuleCreate, Dict[str, Any]]) -> AlertRule:
        """Create a new alert rule.

        Args:
            rule: Alert rule configuration

        Returns:
            Created alert rule
        """
        if isinstance(rule, AlertRuleCreate):
            rule = rule.__dict__
        data = await self._request("POST", "/api/alerts", json=rule)
        return AlertRule(**data)

    async def get_alert_rule(self, rule_id: str) -> AlertRule:
        """Retrieve an alert rule.

        Args:
            rule_id: Alert rule ID

        Returns:
            Alert rule data
        """
        data = await self._request("GET", f"/api/alerts/{rule_id}")
        return AlertRule(**data)

    async def update_alert_rule(
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
        data = await self._request("PUT", f"/api/alerts/{rule_id}", json=updates)
        return AlertRule(**data)

    async def delete_alert_rule(self, rule_id: str) -> None:
        """Delete an alert rule.

        Args:
            rule_id: Alert rule ID
        """
        await self._request("DELETE", f"/api/alerts/{rule_id}")

    async def list_alert_rules(
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
        data = await self._request("GET", "/api/alerts", params=params)
        return AlertRuleListResponse(**data)

    # Metrics Methods

    async def query_metrics(self, query: Union[MetricsQuery, Dict[str, Any]]) -> MetricsResponse:
        """Query time series metrics data.

        Args:
            query: Metrics query parameters

        Returns:
            Metrics data response
        """
        if isinstance(query, MetricsQuery):
            query = query.__dict__
        data = await self._request("GET", "/api/metrics", params=query)
        return MetricsResponse(**data)
