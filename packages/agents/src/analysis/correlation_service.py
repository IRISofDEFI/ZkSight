"""Correlation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .models import DataSeries, CorrelationResult


@dataclass
class CorrelationAnalyzer:
    """Computes Pearson correlations for metric pairs."""

    minimum_points: int = 5
    significance_threshold: float = 0.05

    def analyze(self, series_collection: Sequence[DataSeries]) -> List[CorrelationResult]:
        """Compute correlations for every pair of series."""
        results: List[CorrelationResult] = []
        for first, second in _pairwise(series_collection):
            coeff = _pearson(first.values(), second.values())
            if coeff is None:
                continue
            p_value = _approximate_p_value(coeff, len(first.points))
            results.append(
                CorrelationResult(
                    metric_a=first.metric,
                    metric_b=second.metric,
                    coefficient=coeff,
                    p_value=p_value,
                    significant=p_value < self.significance_threshold,
                    lag=0,
                )
            )
        return results


def _pairwise(series_collection: Sequence[DataSeries]) -> Iterable[Tuple[DataSeries, DataSeries]]:
    for idx, first in enumerate(series_collection):
        for jdx in range(idx + 1, len(series_collection)):
            second = series_collection[jdx]
            min_length = min(len(first.points), len(second.points))
            if min_length < 2:
                continue
            yield (
                DataSeries(metric=first.metric, points=first.points[:min_length]),
                DataSeries(metric=second.metric, points=second.points[:min_length]),
            )


def _pearson(values_a: Sequence[float], values_b: Sequence[float]) -> float | None:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return None
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    numerator = sum(
        (a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b)
    )
    denom_a = sum((a - mean_a) ** 2 for a in values_a) ** 0.5
    denom_b = sum((b - mean_b) ** 2 for b in values_b) ** 0.5
    if denom_a == 0 or denom_b == 0:
        return None
    return numerator / (denom_a * denom_b)


def _approximate_p_value(coefficient: float, sample_size: int) -> float:
    if sample_size <= 2:
        return 1.0
    # Simple approximation based on student's t distribution
    t_stat = abs(coefficient) * ((sample_size - 2) ** 0.5) / (1 - coefficient ** 2) ** 0.5
    # Convert to pseudo p-value (two-tailed) using logistic approximation
    return 2 * (1 / (1 + (t_stat ** 2)))

