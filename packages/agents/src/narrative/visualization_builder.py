"""Visualization configuration builders."""
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..analysis.models import DataSeries, AnalysisResultBundle

logger = logging.getLogger(__name__)


@dataclass
class Visualization:
    """Visualization model."""

    id: str
    type: str
    data_json: str
    config_json: str
    description: str


class VisualizationBuilder:
    """Builds visualization configurations."""

    def build_visualizations(
        self, analysis_results: AnalysisResultBundle
    ) -> List[Visualization]:
        """
        Build visualizations from analysis results.

        Args:
            analysis_results: Analysis results bundle

        Returns:
            List of visualization configurations
        """
        visualizations = []

        # Time series line charts for statistics
        for stat in analysis_results.statistics[:5]:
            if stat.series and len(stat.series.points) > 0:
                viz = self._build_line_chart(stat.series, stat.metric)
                visualizations.append(viz)

        # Scatter plot for correlations
        if analysis_results.correlations:
            viz = self._build_correlation_scatter(analysis_results.correlations)
            visualizations.append(viz)

        # Anomaly markers
        if analysis_results.anomalies:
            viz = self._build_anomaly_chart(analysis_results.anomalies)
            visualizations.append(viz)

        return visualizations

    def _build_line_chart(self, series: DataSeries, metric: str) -> Visualization:
        """Build line chart configuration."""
        data = {
            "x": [p.timestamp for p in series.points],
            "y": [p.value for p in series.points],
            "type": "scatter",
            "mode": "lines+markers",
            "name": metric,
        }

        config = {
            "title": f"{metric} Over Time",
            "xaxis": {"title": "Time"},
            "yaxis": {"title": metric},
        }

        return Visualization(
            id=f"line_{metric}",
            type="line",
            data_json=json.dumps([data]),
            config_json=json.dumps(config),
            description=f"Time series chart showing {metric} over time",
        )

    def _build_correlation_scatter(
        self, correlations: List[Any]
    ) -> Visualization:
        """Build correlation scatter plot."""
        data = {
            "x": [c.coefficient for c in correlations],
            "y": [abs(c.coefficient) for c in correlations],
            "text": [
                f"{c.metric1} vs {c.metric2}" for c in correlations
            ],
            "type": "scatter",
            "mode": "markers",
        }

        config = {
            "title": "Correlation Analysis",
            "xaxis": {"title": "Correlation Coefficient"},
            "yaxis": {"title": "Absolute Value"},
        }

        return Visualization(
            id="correlation_scatter",
            type="scatter",
            data_json=json.dumps([data]),
            config_json=json.dumps(config),
            description="Scatter plot showing correlation coefficients",
        )

    def _build_anomaly_chart(self, anomalies: List[Any]) -> Visualization:
        """Build anomaly visualization."""
        data = {
            "x": [a.timestamp for a in anomalies],
            "y": [a.value for a in anomalies],
            "text": [a.metric for a in anomalies],
            "type": "scatter",
            "mode": "markers",
            "marker": {
                "color": [
                    "red" if a.severity == "high" else "orange"
                    if a.severity == "medium"
                    else "yellow"
                    for a in anomalies
                ],
                "size": 10,
            },
        }

        config = {
            "title": "Anomalies Detected",
            "xaxis": {"title": "Time"},
            "yaxis": {"title": "Value"},
        }

        return Visualization(
            id="anomalies",
            type="scatter",
            data_json=json.dumps([data]),
            config_json=json.dumps(config),
            description="Scatter plot highlighting detected anomalies",
        )

