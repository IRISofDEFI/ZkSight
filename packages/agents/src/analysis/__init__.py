"""Analysis package exposing statistical services and the AnalysisAgent."""
from .models import (
    DataSeries,
    AnalysisResultBundle,
    AnomalyResult,
    CorrelationResult,
    PatternResult,
    StatisticSummary,
)
from .statistics_service import StatisticsCalculator
from .anomaly_detector import ZScoreAnomalyDetector
from .correlation_service import CorrelationAnalyzer
from .pattern_detector import PatternDetector
from .significance_service import SignificanceTester
from .pipeline import AnalysisPipeline
from .storage import AnalysisResultRepository
from .agent import AnalysisAgent

__all__ = [
    "DataSeries",
    "AnalysisResultBundle",
    "AnomalyResult",
    "CorrelationResult",
    "PatternResult",
    "StatisticSummary",
    "StatisticsCalculator",
    "ZScoreAnomalyDetector",
    "CorrelationAnalyzer",
    "PatternDetector",
    "SignificanceTester",
    "AnalysisPipeline",
    "AnalysisResultRepository",
    "AnalysisAgent",
]

