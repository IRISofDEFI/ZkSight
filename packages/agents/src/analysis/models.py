"""Shared dataclasses for analysis computations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class DataPoint:
    """Represents a single metric datapoint."""

    timestamp: int
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DataSeries:
    """A time ordered series for one metric."""

    metric: str
    points: Sequence[DataPoint]

    def values(self) -> List[float]:
        """Return just the numeric values."""
        return [point.value for point in self.points]


@dataclass(frozen=True)
class StatisticSummary:
    """Basic descriptive statistics for a metric."""

    metric: str
    mean: float
    median: float
    standard_deviation: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class AnomalyResult:
    """Represents an anomaly detection output."""

    metric: str
    timestamp: int
    value: float
    expected_value: float
    deviation_score: float
    severity: str
    context: str = ""


@dataclass(frozen=True)
class CorrelationResult:
    """Represents a correlation analysis output."""

    metric_a: str
    metric_b: str
    coefficient: float
    p_value: float
    significant: bool
    lag: int = 0


@dataclass(frozen=True)
class PatternResult:
    """Represents detected temporal patterns."""

    metric: str
    pattern_type: str
    description: str
    confidence: float
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResultBundle:
    """Container for analysis pipeline outputs."""

    statistics: List[StatisticSummary] = field(default_factory=list)
    anomalies: List[AnomalyResult] = field(default_factory=list)
    correlations: List[CorrelationResult] = field(default_factory=list)
    patterns: List[PatternResult] = field(default_factory=list)

