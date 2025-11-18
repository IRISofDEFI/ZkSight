"""Tests for analysis pipeline components."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from src.analysis.anomaly_detector import ZScoreAnomalyDetector
from src.analysis.correlation_service import CorrelationAnalyzer
from src.analysis.models import AnalysisResultBundle, DataPoint, DataSeries
from src.analysis.pattern_detector import PatternDetector
from src.analysis.pipeline import AnalysisPipeline
from src.analysis.significance_service import SignificanceTester
from src.analysis.statistics_service import StatisticsCalculator


def _series(metric: str, values: List[float]) -> DataSeries:
    base_ts = int(datetime.utcnow().timestamp() * 1000)
    points = [
        DataPoint(timestamp=base_ts + idx * 60000, value=value, tags={})
        for idx, value in enumerate(values)
    ]
    return DataSeries(metric=metric, points=points)


def test_pipeline_generates_outputs():
    """Pipeline returns structured results for multiple series."""
    pipeline = AnalysisPipeline(
        statistics_calculator=StatisticsCalculator(),
        anomaly_detector=ZScoreAnomalyDetector(z_threshold=1.5, minimum_points=5),
        correlation_analyzer=CorrelationAnalyzer(),
        pattern_detector=PatternDetector(trend_window=3, min_confidence=0.1),
        significance_tester=SignificanceTester(
            anomaly_score_threshold=0.5,
            correlation_pvalue_threshold=0.6,
        ),
    )

    series_a = _series("metric_a", [1, 2, 3, 4, 8, 9, 10])
    series_b = _series("metric_b", [2, 3, 4, 5, 6, 7, 8])

    results: AnalysisResultBundle = pipeline.run([series_a, series_b])

    assert len(results.statistics) == 2
    assert results.anomalies, "Expected anomalies to be detected"
    assert results.correlations, "Expected correlations"
    assert results.patterns, "Expected patterns"


def test_zscore_detector_respects_threshold():
    detector = ZScoreAnomalyDetector(z_threshold=1.0, minimum_points=5)
    normal_series = _series("steady_metric", [10, 10, 10, 10, 10, 10, 10])
    anomalies = detector.detect(normal_series)
    assert anomalies == []


def test_correlation_analyzer_handles_identical_series():
    analyzer = CorrelationAnalyzer()
    series_a = _series("metric_a", [1, 2, 3, 4, 5])
    series_b = _series("metric_b", [1, 2, 3, 4, 5])
    results = analyzer.analyze([series_a, series_b])
    assert results[0].coefficient == 1.0

