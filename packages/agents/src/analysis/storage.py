"""Storage helpers for analysis results."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Iterable, Protocol

from .models import (
    AnalysisResultBundle,
    AnomalyResult,
    CorrelationResult,
    PatternResult,
    StatisticSummary,
)

logger = logging.getLogger(__name__)


class MetricsWriter(Protocol):
    """Protocol for persistence adapters (InfluxDB, Mongo, etc.)."""

    def write_records(self, measurement: str, records: Iterable[dict]) -> None:  # pragma: no cover - interface
        ...


class AnalysisResultRepository:
    """Persists analysis outputs using injected writers."""

    def __init__(
        self,
        statistics_writer: MetricsWriter | None = None,
        anomaly_writer: MetricsWriter | None = None,
        correlation_writer: MetricsWriter | None = None,
        pattern_writer: MetricsWriter | None = None,
    ) -> None:
        self.statistics_writer = statistics_writer
        self.anomaly_writer = anomaly_writer
        self.correlation_writer = correlation_writer
        self.pattern_writer = pattern_writer

    def save(self, results: AnalysisResultBundle) -> None:
        """Persist results using any configured writers."""
        if self.statistics_writer:
            self.statistics_writer.write_records(
                measurement="analysis_statistics",
                records=[_summary_to_record(summary) for summary in results.statistics],
            )
        if self.anomaly_writer:
            self.anomaly_writer.write_records(
                measurement="analysis_anomalies",
                records=[_anomaly_to_record(anomaly) for anomaly in results.anomalies],
            )
        if self.correlation_writer:
            self.correlation_writer.write_records(
                measurement="analysis_correlations",
                records=[_correlation_to_record(correlation) for correlation in results.correlations],
            )
        if self.pattern_writer:
            self.pattern_writer.write_records(
                measurement="analysis_patterns",
                records=[_pattern_to_record(pattern) for pattern in results.patterns],
            )

        if not any(
            [self.statistics_writer, self.anomaly_writer, self.correlation_writer, self.pattern_writer]
        ):
            logger.debug(
                "AnalysisResultRepository.save called without writers; "
                "results retained in-memory only."
            )


def _summary_to_record(summary: StatisticSummary) -> dict:
    return asdict(summary)


def _anomaly_to_record(anomaly: AnomalyResult) -> dict:
    record = asdict(anomaly)
    record["tags"] = json.dumps(anomaly.context)
    return record


def _correlation_to_record(correlation: CorrelationResult) -> dict:
    return asdict(correlation)


def _pattern_to_record(pattern: PatternResult) -> dict:
    record = asdict(pattern)
    record["parameters"] = json.dumps(pattern.parameters)
    return record

