"""Descriptive statistics utilities."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Sequence

from .models import StatisticSummary, DataSeries


@dataclass
class StatisticsCalculator:
    """Calculates descriptive statistics for a metric series."""

    def summarize(self, series: DataSeries) -> StatisticSummary:
        """Return StatisticSummary for provided series."""
        values = [value for value in series.values() if value is not None]
        if not values:
            raise ValueError("StatisticsCalculator requires at least one numeric value.")

        return StatisticSummary(
            metric=series.metric,
            mean=_safe_mean(values),
            median=_safe_median(values),
            standard_deviation=_population_std(values),
            minimum=min(values),
            maximum=max(values),
        )

    def summarize_many(self, series_list: Sequence[DataSeries]) -> Sequence[StatisticSummary]:
        """Summarize multiple metrics."""
        return [self.summarize(series) for series in series_list]


def _safe_mean(values: Sequence[float]) -> float:
    return mean(values) if len(values) > 1 else float(values[0])


def _safe_median(values: Sequence[float]) -> float:
    return median(values)


def _population_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return variance ** 0.5

