"""Pattern detection heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import DataSeries, PatternResult


@dataclass
class PatternDetector:
    """Detects simple moving-average based patterns."""

    trend_window: int = 5
    min_confidence: float = 0.6

    def detect(self, series: DataSeries) -> List[PatternResult]:
        """Return high-level patterns derived from slope analysis."""
        values = series.values()
        if len(values) < self.trend_window + 2:
            return []

        results: List[PatternResult] = []
        slope = _slope(values[-self.trend_window :])
        if abs(slope) < 1e-5:
            return results

        pattern_type = "trend_up" if slope > 0 else "trend_down"
        confidence = min(0.95, abs(slope) * 10)

        if confidence >= self.min_confidence:
            description = (
                f"{series.metric} shows a {pattern_type.replace('_', ' ')} "
                f"with slope {slope:.4f}"
            )
            results.append(
                PatternResult(
                    metric=series.metric,
                    pattern_type=pattern_type,
                    description=description,
                    confidence=confidence,
                    parameters={"slope": slope},
                )
            )
        return results


def _slope(values: List[float]) -> float:
    count = len(values)
    if count < 2:
        return 0.0
    x_vals = list(range(count))
    mean_x = sum(x_vals) / count
    mean_y = sum(values) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, values))
    denominator = sum((x - mean_x) ** 2 for x in x_vals)
    return numerator / denominator if denominator else 0.0

