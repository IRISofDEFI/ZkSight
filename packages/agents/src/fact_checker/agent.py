"""Fact-Checker Agent implementation."""
import logging
from typing import Dict, Type, Any, Optional
from ..messaging import BaseAgent, ConnectionPool, create_metadata
from ..config import AgentConfig
from .claim_extractor import ClaimExtractor
from .verification_manager import VerificationManager
from .conflict_detector import ConflictDetector
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

try:
    from ..messaging.generated import messages_pb2

    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False

    class messages_pb2:
        class NarrativeResponse:
            pass

        class FactCheckRequest:
            pass

        class FactCheckResponse:
            pass


class FactCheckerAgent(BaseAgent):
    """Verifies claims in generated narratives."""

    AGENT_NAME = "fact_checker_agent"
    EXCHANGE_NAME = "chimera.events"

    ROUTING_KEY_NARRATIVE_GENERATED = "narrative.generated"
    ROUTING_KEY_FACT_CHECK_REQUEST = "fact_check.request"
    ROUTING_KEY_FACT_CHECK_RESULT = "fact_check.result"

    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        claim_extractor: Optional[ClaimExtractor] = None,
        verification_manager: Optional[VerificationManager] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        """
        Initialize Fact-Checker Agent.

        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            claim_extractor: Optional claim extractor
            verification_manager: Optional verification manager
            conflict_detector: Optional conflict detector
            audit_logger: Optional audit logger
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[
                self.ROUTING_KEY_NARRATIVE_GENERATED,
                self.ROUTING_KEY_FACT_CHECK_REQUEST,
            ],
        )

        self.config = config
        self.claim_extractor = claim_extractor or ClaimExtractor()
        self.verification_manager = verification_manager or VerificationManager()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.audit_logger = audit_logger or AuditLogger(config)

        logger.info(f"{self.AGENT_NAME} initialized")

    def get_routing_key_map(self) -> Dict[str, Type]:
        """Get routing key to message class mapping."""
        if not PROTO_AVAILABLE:
            return {}
        return {
            self.ROUTING_KEY_NARRATIVE_GENERATED: messages_pb2.NarrativeResponse,
            self.ROUTING_KEY_FACT_CHECK_REQUEST: messages_pb2.FactCheckRequest,
        }

    def route_message(
        self, message: Any, routing_key: str, properties: Dict[str, Any]
    ) -> None:
        """Route message to appropriate handler."""
        if routing_key == self.ROUTING_KEY_NARRATIVE_GENERATED:
            self._handle_narrative_generated(message, properties)
        elif routing_key == self.ROUTING_KEY_FACT_CHECK_REQUEST:
            self._handle_fact_check_request(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_narrative_generated(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle narrative generated message."""
        correlation_id = properties.get("correlation_id")
        try:
            # Extract report text
            report = getattr(message, "report", None)
            if not report:
                return

            report_text = getattr(report, "executive_summary", "")
            for section in getattr(report, "sections", []):
                report_text += " " + getattr(section, "content", "")

            # Extract claims
            claims = self.claim_extractor.extract_claims(report_text)

            if not claims:
                logger.info("No claims extracted from narrative")
                return

            # Verify claims
            import asyncio

            verified_claims = asyncio.run(
                self.verification_manager.verify_claims(claims)
            )

            # Detect conflicts
            evidence_list = [vc.evidence for vc in verified_claims]
            conflicts = self.conflict_detector.detect_conflicts(claims, evidence_list)

            # Log audit trail
            for claim, vc in zip(claims, verified_claims):
                self.audit_logger.log_verification(claim, vc)

            for conflict in conflicts:
                self.audit_logger.log_conflict(conflict)

            # Calculate overall confidence
            overall_confidence = (
                sum(vc.confidence for vc in verified_claims) / len(verified_claims)
                if verified_claims
                else 0.0
            )

            # Publish fact-check result
            self._publish_fact_check_result(
                verified_claims, conflicts, overall_confidence, correlation_id
            )

        except Exception as e:
            logger.error(f"Error handling narrative generated: {e}", exc_info=True)

    def _handle_fact_check_request(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle fact-check request message."""
        correlation_id = properties.get("correlation_id")
        try:
            claims = getattr(message, "claims", [])
            if not claims:
                return

            import asyncio

            verified_claims = asyncio.run(
                self.verification_manager.verify_claims(claims)
            )

            evidence_list = [vc.evidence for vc in verified_claims]
            conflicts = self.conflict_detector.detect_conflicts(claims, evidence_list)

            overall_confidence = (
                sum(vc.confidence for vc in verified_claims) / len(verified_claims)
                if verified_claims
                else 0.0
            )

            self._publish_fact_check_result(
                verified_claims, conflicts, overall_confidence, correlation_id
            )

        except Exception as e:
            logger.error(f"Error handling fact-check request: {e}", exc_info=True)

    def _publish_fact_check_result(
        self,
        verified_claims: list,
        conflicts: list,
        overall_confidence: float,
        correlation_id: Optional[str],
    ) -> None:
        """Publish fact-check result."""
        if not PROTO_AVAILABLE:
            logger.info(
                f"Would publish fact-check result: "
                f"confidence={overall_confidence}, correlation_id={correlation_id}"
            )
            return

        response = messages_pb2.FactCheckResponse()
        response.metadata.CopyFrom(
            create_metadata(self.AGENT_NAME, correlation_id=correlation_id)
        )
        response.overall_confidence = overall_confidence

        # Add verified claims
        for vc in verified_claims:
            vc_msg = response.verified_claims.add()
            vc_msg.claim.id = vc.claim.id
            vc_msg.claim.statement = vc.claim.statement
            vc_msg.claim.metric = vc.claim.metric
            vc_msg.claim.numeric_value = vc.claim.value
            vc_msg.verified = vc.verified
            vc_msg.confidence = vc.confidence
            vc_msg.sources.extend(vc.sources)

        # Add conflicts
        for conflict in conflicts:
            conflict_msg = response.conflicts.add()
            conflict_msg.claim.id = conflict.claim.id
            conflict_msg.resolution = conflict.resolution
            for source in conflict.sources:
                source_msg = conflict_msg.sources.add()
                source_msg.source = source.source
                source_msg.numeric_value = source.value
                source_msg.difference = source.difference

        self.publish_event(
            message=response,
            routing_key=self.ROUTING_KEY_FACT_CHECK_RESULT,
            correlation_id=correlation_id,
        )

        logger.info(f"Published fact-check result: confidence={overall_confidence}")

