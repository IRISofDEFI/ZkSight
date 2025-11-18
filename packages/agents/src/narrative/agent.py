"""Narrative Agent for generating reports from analysis results."""
import logging
import uuid
from typing import Dict, Type, Any, Optional
from ..messaging import BaseAgent, ConnectionPool, create_metadata
from ..config import AgentConfig
from .llm_client import LLMClient
from .report_builder import ReportBuilder
from .visualization_builder import VisualizationBuilder
from .storage import NarrativeStorage

logger = logging.getLogger(__name__)

try:
    from ..messaging.generated import messages_pb2

    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False

    class messages_pb2:
        class AnalysisResponse:
            pass

        class NarrativeRequest:
            pass

        class NarrativeResponse:
            pass


class NarrativeAgent(BaseAgent):
    """Generates narrative reports from analysis results."""

    AGENT_NAME = "narrative_agent"
    EXCHANGE_NAME = "chimera.events"

    ROUTING_KEY_ANALYSIS_RESULT = "analysis.result"
    ROUTING_KEY_NARRATIVE_REQUEST = "narrative.request"
    ROUTING_KEY_NARRATIVE_GENERATED = "narrative.generated"
    ROUTING_KEY_NARRATIVE_PROGRESS = "narrative.progress"

    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        llm_client: Optional[LLMClient] = None,
        storage: Optional[NarrativeStorage] = None,
    ):
        """
        Initialize Narrative Agent.

        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            llm_client: Optional LLM client (created if not provided)
            storage: Optional storage (created if not provided)
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[
                self.ROUTING_KEY_ANALYSIS_RESULT,
                self.ROUTING_KEY_NARRATIVE_REQUEST,
            ],
        )

        self.config = config
        self.llm_client = llm_client or LLMClient(config)
        self.report_builder = ReportBuilder(self.llm_client)
        self.viz_builder = VisualizationBuilder()
        self.storage = storage or NarrativeStorage(config)

        logger.info(f"{self.AGENT_NAME} initialized")

    def get_routing_key_map(self) -> Dict[str, Type]:
        """Get routing key to message class mapping."""
        if not PROTO_AVAILABLE:
            return {}
        return {
            self.ROUTING_KEY_ANALYSIS_RESULT: messages_pb2.AnalysisResponse,
            self.ROUTING_KEY_NARRATIVE_REQUEST: messages_pb2.NarrativeRequest,
        }

    def route_message(
        self, message: Any, routing_key: str, properties: Dict[str, Any]
    ) -> None:
        """Route message to appropriate handler."""
        if routing_key == self.ROUTING_KEY_ANALYSIS_RESULT:
            self._handle_analysis_result(message, properties)
        elif routing_key == self.ROUTING_KEY_NARRATIVE_REQUEST:
            self._handle_narrative_request(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_analysis_result(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle analysis result message."""
        correlation_id = properties.get("correlation_id")
        try:
            # Convert proto message to analysis bundle
            analysis_bundle = self._parse_analysis_response(message)
            original_query = getattr(message, "original_query", "Unknown query")

            # Generate report
            report = self._generate_report(analysis_bundle, original_query)

            # Generate visualizations
            visualizations = self.viz_builder.build_visualizations(analysis_bundle)

            # Store report
            report_id = str(uuid.uuid4())
            self.storage.store_report(report, report_id)

            # Publish narrative generated event
            self._publish_narrative_generated(
                report, visualizations, report_id, correlation_id
            )

        except Exception as e:
            logger.error(f"Error handling analysis result: {e}", exc_info=True)

    def _handle_narrative_request(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle narrative request message."""
        correlation_id = properties.get("correlation_id")
        try:
            analysis_response = getattr(message, "analysis_results", None)
            original_query = getattr(message, "original_query", "Unknown query")
            user_expertise = getattr(message, "user_expertise_level", "intermediate")

            if analysis_response:
                analysis_bundle = self._parse_analysis_response(analysis_response)
                report = self._generate_report(
                    analysis_bundle, original_query, user_expertise
                )
                visualizations = self.viz_builder.build_visualizations(
                    analysis_bundle
                )

                report_id = str(uuid.uuid4())
                self.storage.store_report(report, report_id)

                self._publish_narrative_generated(
                    report, visualizations, report_id, correlation_id
                )

        except Exception as e:
            logger.error(f"Error handling narrative request: {e}", exc_info=True)

    def _parse_analysis_response(self, message: Any) -> Any:
        """Parse analysis response message to analysis bundle."""
        # This would convert proto message to AnalysisResultBundle
        # For now, return a placeholder
        from ..analysis.models import AnalysisResultBundle

        return AnalysisResultBundle(
            statistics=[],
            anomalies=[],
            correlations=[],
            patterns=[],
        )

    async def _generate_report(
        self,
        analysis_bundle: Any,
        original_query: str,
        user_expertise: str = "intermediate",
    ) -> Any:
        """Generate report from analysis bundle."""
        import asyncio

        if asyncio.iscoroutinefunction(self.report_builder.build_report):
            return await self.report_builder.build_report(
                analysis_bundle, original_query, user_expertise
            )
        else:
            # Fallback for sync version
            return self.report_builder.build_report(
                analysis_bundle, original_query, user_expertise
            )

    def _publish_narrative_generated(
        self,
        report: Any,
        visualizations: list,
        report_id: str,
        correlation_id: Optional[str],
    ) -> None:
        """Publish narrative generated event."""
        if not PROTO_AVAILABLE:
            logger.info(
                f"Would publish narrative generated: report_id={report_id}, "
                f"correlation_id={correlation_id}"
            )
            return

        response = messages_pb2.NarrativeResponse()
        response.metadata.CopyFrom(
            create_metadata(self.AGENT_NAME, correlation_id=correlation_id)
        )

        # Set report
        response.report.title = report.title
        response.report.executive_summary = report.executive_summary
        response.report.created_at = report.created_at

        for section in report.sections:
            section_msg = response.report.sections.add()
            section_msg.title = section.title
            section_msg.content = section.content
            section_msg.order = section.order

        # Set visualizations
        for viz in visualizations:
            viz_msg = response.visualizations.add()
            viz_msg.id = viz.id
            viz_msg.type = getattr(
                messages_pb2.Visualization.VisualizationType,
                f"VIZ_{viz.type.upper()}",
                messages_pb2.Visualization.VisualizationType.VIZ_UNKNOWN,
            )
            viz_msg.data_json = viz.data_json
            viz_msg.config_json = viz.config_json
            viz_msg.description = viz.description

        # Set export URLs
        response.export_urls["json"] = f"/api/reports/{report_id}/export/json"
        response.export_urls["html"] = f"/api/reports/{report_id}/export/html"

        self.publish_event(
            message=response,
            routing_key=self.ROUTING_KEY_NARRATIVE_GENERATED,
            correlation_id=correlation_id,
        )

        logger.info(f"Published narrative generated: report_id={report_id}")

