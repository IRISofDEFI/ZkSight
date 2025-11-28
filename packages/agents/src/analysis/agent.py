"""AnalysisAgent implementation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Sequence, Type, Any

from ..config import AgentConfig
from ..messaging import BaseAgent, ConnectionPool, create_metadata
from .models import AnalysisResultBundle, DataPoint, DataSeries
from .pipeline import AnalysisPipeline
from .statistics_service import StatisticsCalculator
from .anomaly_detector import ZScoreAnomalyDetector
from .correlation_service import CorrelationAnalyzer
from .pattern_detector import PatternDetector
from .significance_service import SignificanceTester
from .storage import AnalysisResultRepository

# Import tracing utilities
try:
    from ..tracing import trace_agent_operation, set_span_attribute, add_span_event
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from ..messaging.generated import messages_pb2

    PROTO_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    PROTO_AVAILABLE = False

    class messages_pb2:  # type: ignore
        class DataRetrievalResponse:
            data: Dict[str, Any] = {}

        class AnalysisRequest:
            data: Dict[str, Any] = {}

        class AnalysisResponse:
            def __init__(self):
                self.metadata = type("Metadata", (), {})()
                self.correlations = []
                self.anomalies = []
                self.patterns = []
                self.statistics = []

        class ErrorResponse:
            pass


@dataclass
class AnalysisAgent(BaseAgent):
    """Consumes data retrieval outputs and publishes derived insights."""

    connection_pool: ConnectionPool
    config: AgentConfig
    pipeline: AnalysisPipeline | None = None
    repository: AnalysisResultRepository | None = None

    AGENT_NAME = "analysis_agent"
    EXCHANGE_NAME = "chimera.events"

    ROUTING_KEY_DATA_RESPONSE = "data_retrieval.response"
    ROUTING_KEY_ANALYSIS_REQUEST = "analysis.request"
    ROUTING_KEY_ANALYSIS_RESULT = "analysis.result"
    ROUTING_KEY_ERROR = "analysis.error"

    def __post_init__(self) -> None:
        BaseAgent.__init__(
            self,
            connection_pool=self.connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[
                self.ROUTING_KEY_DATA_RESPONSE,
                self.ROUTING_KEY_ANALYSIS_REQUEST,
            ],
            prefetch_count=5,
        )

        if self.pipeline is None:
            self.pipeline = AnalysisPipeline(
                statistics_calculator=StatisticsCalculator(),
                anomaly_detector=ZScoreAnomalyDetector(),
                correlation_analyzer=CorrelationAnalyzer(),
                pattern_detector=PatternDetector(),
                significance_tester=SignificanceTester(),
            )

        if self.repository is None:
            self.repository = AnalysisResultRepository()

    # BaseAgent overrides
    def get_routing_key_map(self) -> Dict[str, Type]:
        if not PROTO_AVAILABLE:
            return {}
        return {
            self.ROUTING_KEY_DATA_RESPONSE: messages_pb2.DataRetrievalResponse,
            self.ROUTING_KEY_ANALYSIS_REQUEST: messages_pb2.AnalysisRequest,
        }

    def route_message(self, message: Any, routing_key: str, properties: Dict[str, Any]) -> None:
        if routing_key == self.ROUTING_KEY_DATA_RESPONSE:
            self._handle_data_response(message, properties)
        elif routing_key == self.ROUTING_KEY_ANALYSIS_REQUEST:
            self._handle_analysis_request(message, properties)
        else:
            logger.warning("AnalysisAgent received unexpected routing key %s", routing_key)

    # Message handlers
    def _handle_data_response(self, message: Any, properties: Dict[str, Any]) -> None:
        correlation_id = properties.get("correlation_id")
        try:
            series = self._series_from_response(message)
            result_bundle = self._run_pipeline(series)
            self.repository.save(result_bundle)
            self._publish_analysis_response(result_bundle, correlation_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to process DataRetrievalResponse: %s", exc)
            self._publish_error(str(exc), correlation_id)

    def _handle_analysis_request(self, message: Any, properties: Dict[str, Any]) -> None:
        correlation_id = properties.get("correlation_id")
        try:
            series = self._series_from_payload(getattr(message, "data", {}))
            result_bundle = self._run_pipeline(series)
            self.repository.save(result_bundle)
            self._publish_analysis_response(result_bundle, correlation_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Failed to process AnalysisRequest: %s", exc)
            self._publish_error(str(exc), correlation_id)

    # Helpers
    def _run_pipeline(self, series_collection: Sequence[DataSeries]) -> AnalysisResultBundle:
        if not series_collection:
            raise ValueError("AnalysisAgent requires at least one metric series.")
        assert self.pipeline is not None
        
        if TRACING_AVAILABLE:
            @trace_agent_operation("run_analysis_pipeline")
            def _run():
                set_span_attribute("analysis.series_count", len(series_collection))
                set_span_attribute("analysis.metrics", ",".join([s.metric for s in series_collection]))
                add_span_event("analysis.pipeline.start")
                result = self.pipeline.run(series_collection)
                add_span_event("analysis.pipeline.complete")
                set_span_attribute("analysis.anomalies_found", len(result.anomalies))
                set_span_attribute("analysis.correlations_found", len(result.correlations))
                set_span_attribute("analysis.patterns_found", len(result.patterns))
                return result
            return _run()
        else:
            return self.pipeline.run(series_collection)

    def _series_from_response(self, message: Any) -> List[DataSeries]:
        data_map = getattr(message, "data", {})
        if hasattr(data_map, "items"):
            return self._series_from_payload(data_map)
        return []

    def _series_from_payload(self, payload: Any) -> List[DataSeries]:
        series_list: List[DataSeries] = []
        for metric, point_list in dict(payload).items():
            points: List[DataPoint] = []
            proto_points = getattr(point_list, "points", []) or point_list
            for proto_point in proto_points:
                value = _extract_numeric_value(proto_point)
                if value is None:
                    continue
                timestamp = getattr(proto_point, "timestamp", 0)
                tags = dict(getattr(proto_point, "tags", {}))
                metric_name = getattr(proto_point, "metric", metric)
                points.append(
                    DataPoint(
                        timestamp=timestamp,
                        value=value,
                        tags=tags,
                    )
                )
            if points:
                series_list.append(DataSeries(metric=metric or metric_name, points=points))
        return series_list

    def _publish_analysis_response(self, results: AnalysisResultBundle, correlation_id: str | None) -> None:
        if not PROTO_AVAILABLE:
            logger.info("Analysis response ready (protobuf unavailable).")
            return

        response = messages_pb2.AnalysisResponse()
        metadata = create_metadata(self.AGENT_NAME, correlation_id)
        response.metadata.message_id = metadata["message_id"]
        response.metadata.correlation_id = metadata["correlation_id"]
        response.metadata.timestamp = metadata["timestamp"]
        response.metadata.sender_agent = metadata["sender_agent"]
        response.metadata.reply_to = metadata["reply_to"]

        _fill_statistics(response, results)
        _fill_anomalies(response, results)
        _fill_correlations(response, results)
        _fill_patterns(response, results)

        self.publish_event(
            message=response,
            routing_key=self.ROUTING_KEY_ANALYSIS_RESULT,
            correlation_id=metadata["correlation_id"],
        )

    def _publish_error(self, error_message: str, correlation_id: str | None) -> None:
        if not PROTO_AVAILABLE:
            logger.error("Analysis error (protobuf unavailable): %s", error_message)
            return

        error = messages_pb2.ErrorResponse()
        metadata = create_metadata(self.AGENT_NAME, correlation_id)
        error.metadata.message_id = metadata["message_id"]
        error.metadata.correlation_id = metadata["correlation_id"]
        error.metadata.timestamp = metadata["timestamp"]
        error.metadata.sender_agent = metadata["sender_agent"]
        error.error_code = "analysis_error"
        error.error_message = error_message
        error.retryable = False

        self.publish_event(
            message=error,
            routing_key=self.ROUTING_KEY_ERROR,
            correlation_id=metadata["correlation_id"],
        )


def _extract_numeric_value(point: Any) -> float | None:
    if hasattr(point, "numeric_value"):
        return getattr(point, "numeric_value")
    if hasattr(point, "value"):
        return getattr(point, "value")
    if isinstance(point, dict):
        return point.get("numeric_value") or point.get("value")
    return None


def _fill_statistics(response: Any, results: AnalysisResultBundle) -> None:
    for summary in results.statistics:
        stat_msg = response.statistics.add()
        stat_msg.metric = summary.metric
        stat_msg.mean = summary.mean
        stat_msg.median = summary.median
        stat_msg.std_dev = summary.standard_deviation
        stat_msg.min = summary.minimum
        stat_msg.max = summary.maximum


def _fill_anomalies(response: Any, results: AnalysisResultBundle) -> None:
    for anomaly in results.anomalies:
        anomaly_msg = response.anomalies.add()
        severity = getattr(messages_pb2.Anomaly.Severity, anomaly.severity, 0)
        anomaly_msg.metric = anomaly.metric
        anomaly_msg.timestamp = anomaly.timestamp
        anomaly_msg.value = anomaly.value
        anomaly_msg.expected_value = anomaly.expected_value
        anomaly_msg.deviation_score = anomaly.deviation_score
        anomaly_msg.severity = severity
        anomaly_msg.context = anomaly.context


def _fill_correlations(response: Any, results: AnalysisResultBundle) -> None:
    for correlation in results.correlations:
        corr_msg = response.correlations.add()
        corr_msg.metric1 = correlation.metric_a
        corr_msg.metric2 = correlation.metric_b
        corr_msg.coefficient = correlation.coefficient
        corr_msg.p_value = correlation.p_value
        corr_msg.significant = correlation.significant
        corr_msg.lag = correlation.lag


def _fill_patterns(response: Any, results: AnalysisResultBundle) -> None:
    for pattern in results.patterns:
        pattern_msg = response.patterns.add()
        pattern_msg.metric = pattern.metric
        pattern_msg.pattern_type = pattern.pattern_type
        pattern_msg.description = pattern.description
        pattern_msg.confidence = pattern.confidence
        for key, value in pattern.parameters.items():
            pattern_msg.parameters[key] = value

