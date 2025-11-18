"""Follow-up Agent implementation."""
import logging
from typing import Dict, Type, Any, Optional, List
import redis
from ..messaging import BaseAgent, ConnectionPool, create_metadata
from ..config import AgentConfig
from .question_generator import QuestionGenerator, Suggestion
from .relevance_ranker import RelevanceRanker
from .exploration_tracker import ExplorationTracker
from ..narrative.llm_client import LLMClient

logger = logging.getLogger(__name__)

try:
    from ..messaging.generated import messages_pb2

    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False

    class messages_pb2:
        class NarrativeResponse:
            pass

        class FollowUpRequest:
            pass

        class FollowUpResponse:
            pass


class FollowUpAgent(BaseAgent):
    """Generates contextual follow-up questions."""

    AGENT_NAME = "followup_agent"
    EXCHANGE_NAME = "chimera.events"

    ROUTING_KEY_NARRATIVE_GENERATED = "narrative.generated"
    ROUTING_KEY_FOLLOWUP_REQUEST = "followup.request"
    ROUTING_KEY_FOLLOWUP_SUGGESTIONS = "followup.suggestions"

    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        redis_client: Optional[redis.Redis] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        """
        Initialize Follow-up Agent.

        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            redis_client: Optional Redis client
            llm_client: Optional LLM client
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[
                self.ROUTING_KEY_NARRATIVE_GENERATED,
                self.ROUTING_KEY_FOLLOWUP_REQUEST,
            ],
        )

        self.config = config

        if redis_client is None:
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
            )

        if llm_client is None:
            llm_client = LLMClient(config)

        self.question_generator = QuestionGenerator(llm_client)
        self.relevance_ranker = RelevanceRanker()
        self.exploration_tracker = ExplorationTracker(redis_client)

        logger.info(f"{self.AGENT_NAME} initialized")

    def get_routing_key_map(self) -> Dict[str, Type]:
        """Get routing key to message class mapping."""
        if not PROTO_AVAILABLE:
            return {}
        return {
            self.ROUTING_KEY_NARRATIVE_GENERATED: messages_pb2.NarrativeResponse,
            self.ROUTING_KEY_FOLLOWUP_REQUEST: messages_pb2.FollowUpRequest,
        }

    def route_message(
        self, message: Any, routing_key: str, properties: Dict[str, Any]
    ) -> None:
        """Route message to appropriate handler."""
        if routing_key == self.ROUTING_KEY_NARRATIVE_GENERATED:
            self._handle_narrative_generated(message, properties)
        elif routing_key == self.ROUTING_KEY_FOLLOWUP_REQUEST:
            self._handle_followup_request(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_narrative_generated(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle narrative generated message."""
        correlation_id = properties.get("correlation_id")
        try:
            # Extract information from message
            report = getattr(message, "report", None)
            analysis_results = getattr(message, "analysis_results", None)
            original_query = getattr(report, "title", "Unknown query") if report else "Unknown query"

            # Get session ID from context (would be in metadata)
            session_id = properties.get("session_id", "default")

            # Get session history
            session_history = self.exploration_tracker.get_history(session_id)

            # Generate questions
            import asyncio

            suggestions = asyncio.run(
                self.question_generator.generate_questions(
                    original_query, analysis_results, report, session_history
                )
            )

            # Rank suggestions
            data_availability = {s.question: s.data_available for s in suggestions}
            ranked = self.relevance_ranker.rank_suggestions(
                suggestions, session_history, data_availability
            )

            # Publish suggestions
            self._publish_suggestions(ranked, correlation_id)

        except Exception as e:
            logger.error(f"Error handling narrative generated: {e}", exc_info=True)

    def _handle_followup_request(
        self, message: Any, properties: Dict[str, Any]
    ) -> None:
        """Handle follow-up request message."""
        correlation_id = properties.get("correlation_id")
        try:
            original_query = getattr(message, "original_query", "")
            analysis_results = getattr(message, "analysis_results", None)
            report = getattr(message, "report", None)
            session_history = list(getattr(message, "session_history", []))

            session_id = properties.get("session_id", "default")

            import asyncio

            suggestions = asyncio.run(
                self.question_generator.generate_questions(
                    original_query, analysis_results, report, session_history
                )
            )

            data_availability = {s.question: s.data_available for s in suggestions}
            ranked = self.relevance_ranker.rank_suggestions(
                suggestions, session_history, data_availability
            )

            self._publish_suggestions(ranked, correlation_id)

        except Exception as e:
            logger.error(f"Error handling follow-up request: {e}", exc_info=True)

    def _publish_suggestions(
        self, suggestions: List[Suggestion], correlation_id: Optional[str]
    ) -> None:
        """Publish follow-up suggestions."""
        if not PROTO_AVAILABLE:
            logger.info(
                f"Would publish {len(suggestions)} follow-up suggestions, "
                f"correlation_id={correlation_id}"
            )
            return

        response = messages_pb2.FollowUpResponse()
        response.metadata.CopyFrom(
            create_metadata(self.AGENT_NAME, correlation_id=correlation_id)
        )

        for suggestion in suggestions:
            sugg_msg = response.suggestions.add()
            sugg_msg.question = suggestion.question
            sugg_msg.rationale = suggestion.rationale
            sugg_msg.priority = suggestion.priority
            sugg_msg.data_available = suggestion.data_available
            sugg_msg.estimated_complexity = suggestion.estimated_complexity

        self.publish_event(
            message=response,
            routing_key=self.ROUTING_KEY_FOLLOWUP_SUGGESTIONS,
            correlation_id=correlation_id,
        )

        logger.info(f"Published {len(suggestions)} follow-up suggestions")

