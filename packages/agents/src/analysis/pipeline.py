"""Orchestrates analysis across multiple services."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .statistics_service import StatisticsCalculator
from .anomaly_detector import ZScoreAnomalyDetector
from .correlation_service import CorrelationAnalyzer
from .pattern_detector import PatternDetector
from .significance_service import SignificanceTester
from .models import AnalysisResultBundle, DataSeries


@dataclass
class AnalysisPipeline:
    """Coordinates high-level statistical analyses."""

    statistics_calculator: StatisticsCalculator
    anomaly_detector: ZScoreAnomalyDetector
    correlation_analyzer: CorrelationAnalyzer
    pattern_detector: PatternDetector
    significance_tester: SignificanceTester

    def run(self, series_collection: Sequence[DataSeries]) -> AnalysisResultBundle:
        """Execute the full analysis pipeline."""
        statistics = list(
            self.statistics_calculator.summarize_many(series_collection)
        )
        anomalies = self._detect_anomalies(series_collection)
        correlations = self.correlation_analyzer.analyze(series_collection)
        significant_correlations = self.significance_tester.flag_correlations(correlations)
        patterns = self._detect_patterns(series_collection)

        filtered_anomalies = self.significance_tester.filter_anomalies(anomalies)

        return AnalysisResultBundle(
            statistics=statistics,
            anomalies=list(filtered_anomalies),
            correlations=list(significant_correlations),
            patterns=patterns,
        )

    def _detect_anomalies(self, series_collection: Sequence[DataSeries]):
        results = []
        for series in series_collection:
            results.extend(self.anomaly_detector.detect(series))
        return results

    def _detect_patterns(self, series_collection: Sequence[DataSeries]):
        results = []
        for series in series_collection:
            results.extend(self.pattern_detector.detect(series))
        return results

