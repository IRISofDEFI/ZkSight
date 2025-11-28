"""Query Agent for natural language query processing"""
import logging
from typing import Dict, List, Any, Type, Optional
import redis

from ..messaging import BaseAgent, ConnectionPool
from ..config import AgentConfig
from .nlp_pipeline import NLPPipeline
from .entity_recognizer import EntityRecognizer
from .intent_classifier import IntentClassifier, IntentType
from .context_manager import ContextManager
from .clarification import ClarificationEngine

# Import tracing utilities
try:
    from ..tracing import trace_agent_operation, set_span_attribute, add_span_event
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

# Import proto messages when available
try:
    from ..messaging.generated import messages_pb2
    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False
    # Create placeholder for type hints
    class messages_pb2:
        class QueryRequest: pass
        class QueryResponse: pass
        class QueryIntent: pass
        class ExtractedEntity: pass
        class DataSource: pass
        class TimeRange: pass
        class ErrorResponse: pass

logger = logging.getLogger(__name__)


class QueryAgent(BaseAgent):
    """
    Query Agent processes natural language queries.
    
    Responsibilities:
    - Parse natural language queries
    - Extract entities (dates, metrics, Zcash terms)
    - Classify query intent
    - Manage conversation context
    - Handle query clarification
    - Publish parsed queries to Data Retrieval Agent
    """

    AGENT_NAME = "query_agent"
    EXCHANGE_NAME = "chimera.events"

    # Routing keys
    ROUTING_KEY_QUERY_REQUEST = "query.request"
    ROUTING_KEY_QUERY_RESPONSE = "query.response"
    ROUTING_KEY_DATA_RETRIEVAL_REQUEST = "data_retrieval.request"
    ROUTING_KEY_ERROR = "query.error"

    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        redis_client: Optional[redis.Redis] = None,
    ):
        """
        Initialize Query Agent.

        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            redis_client: Redis client for context storage
        """
        # Initialize base agent
        super().__init__(
            connection_pool=connection_pool,
            agent_name=self.AGENT_NAME,
            exchange_name=self.EXCHANGE_NAME,
            routing_keys=[self.ROUTING_KEY_QUERY_REQUEST],
        )

        self.config = config

        # Initialize NLP components
        logger.info("Initializing NLP pipeline...")
        self.nlp_pipeline = NLPPipeline()
        
        logger.info("Initializing entity recognizer...")
        self.entity_recognizer = EntityRecognizer()
        
        logger.info("Initializing intent classifier...")
        self.intent_classifier = IntentClassifier(use_transformer=False)
        
        logger.info("Initializing clarification engine...")
        self.clarification_engine = ClarificationEngine()

        # Initialize context manager
        if redis_client is None:
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
            )
        
        logger.info("Initializing context manager...")
        self.context_manager = ContextManager(redis_client)

        logger.info(f"{self.AGENT_NAME} initialized successfully")

    def get_routing_key_map(self) -> Dict[str, Type]:
        """Get mapping of routing keys to message classes"""
        if not PROTO_AVAILABLE:
            return {}
        
        return {
            self.ROUTING_KEY_QUERY_REQUEST: messages_pb2.QueryRequest,
        }

    def route_message(
        self,
        message: Any,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Route message to appropriate handler.

        Args:
            message: Deserialized message
            routing_key: Message routing key
            properties: Message properties
        """
        if routing_key == self.ROUTING_KEY_QUERY_REQUEST:
            self._handle_query_request(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_query_request(
        self,
        message: Any,
        properties: Dict[str, Any]
    ) -> None:
        """
        Handle incoming query request.

        Args:
            message: QueryRequest message
            properties: Message properties
        """
        try:
            # Extract message fields
            if PROTO_AVAILABLE:
                user_id = message.user_id
                session_id = message.session_id
                query = message.query
                context_dict = dict(message.context) if message.context else {}
            else:
                # Fallback for testing without proto
                user_id = getattr(message, 'user_id', 'test_user')
                session_id = getattr(message, 'session_id', 'test_session')
                query = getattr(message, 'query', '')
                context_dict = {}

            correlation_id = properties.get("correlation_id")

            logger.info(
                f"Processing query from user {user_id}, "
                f"session {session_id}: '{query}'"
            )

            # Process the query
            result = self.process_query(
                query=query,
                user_id=user_id,
                session_id=session_id,
                context_dict=context_dict,
            )

            # Send response
            if result.get("clarification_needed"):
                self._send_query_response(result, correlation_id)
            else:
                # Send to Data Retrieval Agent
                self._send_data_retrieval_request(result, correlation_id)
                # Also send response to user
                self._send_query_response(result, correlation_id)

        except Exception as e:
            logger.error(f"Error handling query request: {e}", exc_info=True)
            self._send_error_response(str(e), properties.get("correlation_id"))

    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language query.

        Args:
            query: Query text
            user_id: User identifier
            session_id: Session identifier
            context_dict: Optional context from request

        Returns:
            Dictionary with processed query information
        """
        if TRACING_AVAILABLE:
            @trace_agent_operation("process_query")
            def _process():
                set_span_attribute("query.text", query[:100])  # Truncate for privacy
                set_span_attribute("query.user_id", user_id)
                set_span_attribute("query.session_id", session_id)
                return self._process_query_impl(query, user_id, session_id, context_dict)
            return _process()
        else:
            return self._process_query_impl(query, user_id, session_id, context_dict)
    
    def _process_query_impl(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Internal implementation of query processing."""
        # Step 1: Get conversation context
        context = self.context_manager.get_context(session_id) or {}
        
        # Merge with provided context
        if context_dict:
            context.update(context_dict)

        # Step 2: Process with NLP pipeline
        if TRACING_AVAILABLE:
            add_span_event("nlp.processing.start")
        doc = self.nlp_pipeline.process(query)

        # Step 3: Extract entities
        if TRACING_AVAILABLE:
            add_span_event("entity.extraction.start")
        entities = self.entity_recognizer.recognize_entities(query, doc)
        if TRACING_AVAILABLE:
            set_span_attribute("entities.count", len(entities))

        # Step 4: Classify intent
        if TRACING_AVAILABLE:
            add_span_event("intent.classification.start")
        intent = self.intent_classifier.classify(query, entities)
        if TRACING_AVAILABLE:
            set_span_attribute("intent.type", str(intent.get("intent_type", "")))

        # Step 5: Extract context for current query
        query_context = self.context_manager.extract_context_for_query(
            session_id, query
        )

        # Step 6: Merge context with entities
        enhanced_entities = self.context_manager.merge_context_with_entities(
            entities, query_context
        )

        # Step 7: Check for ambiguity
        clarification = self.clarification_engine.check_for_ambiguity(
            query=query,
            intent=intent,
            entities=enhanced_entities,
            context=query_context,
        )
        if TRACING_AVAILABLE:
            set_span_attribute("clarification.needed", clarification["clarification_needed"])

        # Step 8: Update conversation history
        self.context_manager.add_query_to_history(
            session_id=session_id,
            query=query,
            intent=intent,
            entities=enhanced_entities,
        )

        # Step 9: Determine required data sources
        data_sources = self._determine_data_sources(intent, enhanced_entities)
        if TRACING_AVAILABLE:
            set_span_attribute("data_sources.count", len(data_sources))

        return {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "intent": intent,
            "entities": enhanced_entities,
            "data_sources": data_sources,
            "clarification_needed": clarification["clarification_needed"],
            "clarification_questions": clarification.get("questions", []),
            "clarification_reasons": clarification.get("reasons", []),
        }

    def _determine_data_sources(
        self,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Determine which data sources are needed for the query.

        Args:
            intent: Classified intent
            entities: Extracted entities

        Returns:
            List of data source specifications
        """
        data_sources = []

        # Extract metrics to determine sources
        metrics = intent.get("metrics", [])
        
        # Map metrics to data sources
        blockchain_metrics = [
            "shielded_transactions", "transparent_transactions",
            "shielded_pool_size", "block_height", "hash_rate",
            "difficulty", "transaction_fees", "transaction_volume"
        ]
        
        market_metrics = [
            "price", "trading_volume", "market_cap"
        ]
        
        social_metrics = [
            "social_sentiment", "developer_activity"
        ]

        needs_blockchain = any(m in blockchain_metrics for m in metrics)
        needs_market = any(m in market_metrics for m in metrics)
        needs_social = any(m in social_metrics for m in metrics)

        # If no specific metrics, default to blockchain
        if not metrics:
            needs_blockchain = True

        if needs_blockchain:
            data_sources.append({
                "type": "DATA_SOURCE_BLOCKCHAIN",
                "name": "zcash_node"
            })

        if needs_market:
            data_sources.append({
                "type": "DATA_SOURCE_EXCHANGE",
                "name": "exchanges"
            })

        if needs_social:
            data_sources.append({
                "type": "DATA_SOURCE_SOCIAL",
                "name": "social_platforms"
            })

        return data_sources

    def _send_query_response(
        self,
        result: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """Send query response message"""
        if not PROTO_AVAILABLE:
            logger.info(
                f"Would send query response (proto not available): "
                f"clarification_needed={result['clarification_needed']}"
            )
            return

        # Build response message
        response = messages_pb2.QueryResponse()
        
        # Set intent
        intent_type = result["intent"]["intent_type"]
        if isinstance(intent_type, IntentType):
            response.intent.type = getattr(
                messages_pb2.QueryIntent,
                intent_type.value
            )
        
        # Set time range if available
        time_range = result["intent"].get("time_range")
        if time_range:
            response.intent.time_range.start_timestamp = time_range["start_timestamp"]
            response.intent.time_range.end_timestamp = time_range["end_timestamp"]
        
        # Set metrics
        for metric in result["intent"].get("metrics", []):
            response.intent.metrics.append(metric)

        # Set entities
        for entity in result["entities"]:
            entity_msg = response.entities.add()
            entity_msg.entity_type = entity.get("entity_type", "")
            entity_msg.value = str(entity.get("value", ""))
            entity_msg.confidence = entity.get("confidence", 0.0)

        # Set data sources
        for source in result["data_sources"]:
            source_msg = response.required_data_sources.add()
            source_msg.type = getattr(
                messages_pb2.DataSourceType,
                source["type"]
            )
            source_msg.name = source["name"]

        # Set clarification
        response.clarification_needed = result["clarification_needed"]
        for question in result.get("clarification_questions", []):
            response.clarification_questions.append(question)

        # Publish response
        self.publish_response(
            message=response,
            routing_key=self.ROUTING_KEY_QUERY_RESPONSE,
            correlation_id=correlation_id,
        )

        logger.info(f"Sent query response: correlation_id={correlation_id}")

    def _send_data_retrieval_request(
        self,
        result: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """Send data retrieval request to Data Retrieval Agent"""
        if not PROTO_AVAILABLE:
            logger.info(
                f"Would send data retrieval request (proto not available): "
                f"sources={len(result['data_sources'])}"
            )
            return

        # Build request message
        request = messages_pb2.DataRetrievalRequest()

        # Set data sources
        for source in result["data_sources"]:
            source_msg = request.sources.add()
            source_msg.type = getattr(
                messages_pb2.DataSourceType,
                source["type"]
            )
            source_msg.name = source["name"]

        # Set time range
        time_range = result["intent"].get("time_range")
        if time_range:
            request.time_range.start_timestamp = time_range["start_timestamp"]
            request.time_range.end_timestamp = time_range["end_timestamp"]

        # Set metrics
        for metric in result["intent"].get("metrics", []):
            request.metrics.append(metric)

        # Publish request
        self.publish_event(
            message=request,
            routing_key=self.ROUTING_KEY_DATA_RETRIEVAL_REQUEST,
            correlation_id=correlation_id,
        )

        logger.info(
            f"Sent data retrieval request: correlation_id={correlation_id}"
        )

    def _send_error_response(
        self,
        error_message: str,
        correlation_id: Optional[str]
    ) -> None:
        """Send error response"""
        if not PROTO_AVAILABLE:
            logger.error(f"Error (proto not available): {error_message}")
            return

        error = messages_pb2.ErrorResponse()
        error.error_code = "QUERY_PROCESSING_ERROR"
        error.error_message = error_message
        error.retryable = False

        if correlation_id:
            self.publish_response(
                message=error,
                routing_key=self.ROUTING_KEY_ERROR,
                correlation_id=correlation_id,
            )

        logger.error(f"Sent error response: {error_message}")


def create_query_agent(config: Optional[AgentConfig] = None) -> QueryAgent:
    """
    Factory function to create Query Agent.

    Args:
        config: Optional agent configuration

    Returns:
        Initialized QueryAgent instance
    """
    if config is None:
        from ..config import load_config
        config = load_config()

    # Create connection pool
    from ..messaging import get_connection_pool
    connection_pool = get_connection_pool(
        host=config.rabbitmq.host,
        port=config.rabbitmq.port,
        username=config.rabbitmq.username,
        password=config.rabbitmq.password,
        vhost=config.rabbitmq.vhost,
    )

    # Create agent
    agent = QueryAgent(
        connection_pool=connection_pool,
        config=config,
    )

    return agent
