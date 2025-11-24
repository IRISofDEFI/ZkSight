"""Simple z-score based anomaly detection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .models import DataSeries, AnomalyResult


@dataclass
class ZScoreAnomalyDetector:
    """Detects anomalies using rolling z-score."""

    z_threshold: float = 3.0
    minimum_points: int = 10

    def detect(self, series: DataSeries) -> List[AnomalyResult]:
        """Return list of detected anomalies for provided series."""
        values = series.values()
        if len(values) < self.minimum_points:
            return []

        rolling_mean = _rolling_mean(values)
        rolling_std = _rolling_std(values)

        results: List[AnomalyResult] = []
        for idx, point in enumerate(series.points):
            std_value = rolling_std[idx]
            if std_value == 0:
                continue

            deviation_score = abs(point.value - rolling_mean[idx]) / std_value
            if deviation_score >= self.z_threshold:
                severity = self._severity_for_score(deviation_score)
                results.append(
                    AnomalyResult(
                        metric=series.metric,
                        timestamp=point.timestamp,
                        value=point.value,
                        expected_value=rolling_mean[idx],
                        deviation_score=deviation_score,
                        severity=severity,
                        context=point.tags.get("context", ""),
                    )
                )
        return results

    def _severity_for_score(self, score: float) -> str:
        if score >= self.z_threshold + 2.0:
            return "SEVERITY_HIGH"
        if score >= self.z_threshold + 1.0:
            return "SEVERITY_MEDIUM"
        return "SEVERITY_LOW"


def _rolling_mean(values: Sequence[float], window: int = 5) -> List[float]:
    padded = [values[0]] * (window - 1) + list(values)
    means: List[float] = []
    for idx in range(len(values)):
        window_values = padded[idx : idx + window]
        means.append(sum(window_values) / window)
    return means


def _rolling_std(values: Sequence[float], window: int = 5) -> List[float]:
    padded = [values[0]] * (window - 1) + list(values)
    stds: List[float] = []
    for idx in range(len(values)):
        window_values = padded[idx : idx + window]
        avg = sum(window_values) / window
        variance = sum((value - avg) ** 2 for value in window_values) / window
        stds.append(variance ** 0.5)
    return stds

