"""Significance helpers for analysis results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .models import CorrelationResult, AnomalyResult


@dataclass
class SignificanceTester:
    """Applies lightweight heuristics for statistical significance."""

    anomaly_score_threshold: float = 2.5
    correlation_pvalue_threshold: float = 0.05

    def filter_anomalies(self, anomalies: Sequence[AnomalyResult]) -> Sequence[AnomalyResult]:
        """Return anomalies that meet score requirement."""
        return [
            anomaly
            for anomaly in anomalies
            if anomaly.deviation_score >= self.anomaly_score_threshold
        ]

    def flag_correlations(self, correlations: Sequence[CorrelationResult]) -> Sequence[CorrelationResult]:
        """Return correlations that meet p-value requirement."""
        return [
            correlation
            for correlation in correlations
            if correlation.p_value <= self.correlation_pvalue_threshold
        ]

