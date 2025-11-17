"""Example agent using the BaseAgent class"""
import logging
from typing import Dict, Any, Type
from google.protobuf.message import Message as ProtoMessage

from ..connection import ConnectionPool
from ..base_agent import BaseAgent
from ...config import load_config

# Note: Import generated protobuf messages after running proto generation
# from ..generated import messages_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryAgent(BaseAgent):
    """
    Example Query Agent implementation using BaseAgent.
    
    Demonstrates:
    - Routing key mapping
    - Message routing
    - Request-response pattern
    - Correlation ID tracking
    """

    def __init__(self, connection_pool: ConnectionPool):
        """
        Initialize Query Agent

        Args:
            connection_pool: RabbitMQ connection pool
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name="query_agent",
            exchange_name="chimera.events",
            routing_keys=[
                "query.request",      # User queries
                "data.response",      # Data retrieval responses
                "analysis.response",  # Analysis responses
            ],
            prefetch_count=1,
        )

    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        """
        Map routing keys to Protocol Buffer message classes.

        Returns:
            Dictionary mapping routing keys to message classes
        """
        # This would use the generated protobuf classes
        # return {
        #     "query.request": messages_pb2.QueryRequest,
        #     "data.response": messages_pb2.DataRetrievalResponse,
        #     "analysis.response": messages_pb2.AnalysisResponse,
        # }
        
        # Placeholder for demonstration
        from google.protobuf.message import Message
        return {
            "query.request": Message,
            "data.response": Message,
            "analysis.response": Message,
        }

    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Route message to appropriate handler.

        Args:
            message: Deserialized Protocol Buffer message
            routing_key: Routing key of the message
            properties: Message properties
        """
        correlation_id = properties.get("correlation_id")

        # Route based on routing key
        if routing_key == "query.request":
            self._handle_query_request(message, correlation_id)
        elif routing_key == "data.response":
            self._handle_data_response(message, correlation_id)
        elif routing_key == "analysis.response":
            self._handle_analysis_response(message, correlation_id)
        else:
            logger.warning(f"Unhandled routing key: {routing_key}")

    def _handle_query_request(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """
        Handle incoming query request from user.

        Args:
            message: QueryRequest message
            correlation_id: Correlation ID from request
        """
        logger.info(f"Processing query request: {correlation_id}")

        # Parse the query (NLP processing would go here)
        # query_text = message.query
        # intent = self._parse_intent(query_text)
        # entities = self._extract_entities(query_text)

        # Request data from Data Retrieval Agent
        # data_request = messages_pb2.DataRetrievalRequest()
        # data_request.metadata.CopyFrom(create_metadata(self.agent_name, correlation_id))
        # data_request.sources.extend(["blockchain", "exchange"])
        # data_request.time_range.start = ...
        # data_request.time_range.end = ...

        # Publish request and track correlation
        # self.publish_request(
        #     message=data_request,
        #     routing_key="data.request",
        #     reply_routing_key="data.response",
        #     context={
        #         "original_query": query_text,
        #         "intent": intent,
        #         "entities": entities,
        #     }
        # )

        logger.info(f"Requested data for query: {correlation_id}")

    def _handle_data_response(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """
        Handle data response from Data Retrieval Agent.

        Args:
            message: DataRetrievalResponse message
            correlation_id: Correlation ID from original request
        """
        logger.info(f"Received data response: {correlation_id}")

        # Get original query context
        context = self.get_correlation_context(correlation_id)
        if not context:
            logger.warning(f"No context found for correlation: {correlation_id}")
            return

        # Extract data from response
        # data_points = message.data
        # metadata = message.metadata

        # Request analysis from Analysis Agent
        # analysis_request = messages_pb2.AnalysisRequest()
        # analysis_request.metadata.CopyFrom(create_metadata(self.agent_name, correlation_id))
        # analysis_request.data.extend(data_points)
        # analysis_request.analysis_types.extend(["correlation", "anomaly"])

        # Publish analysis request
        # self.publish_request(
        #     message=analysis_request,
        #     routing_key="analysis.request",
        #     reply_routing_key="analysis.response",
        #     context=context,  # Pass along original context
        # )

        logger.info(f"Requested analysis for query: {correlation_id}")

    def _handle_analysis_response(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """
        Handle analysis response from Analysis Agent.

        Args:
            message: AnalysisResponse message
            correlation_id: Correlation ID from original request
        """
        logger.info(f"Received analysis response: {correlation_id}")

        # Get original query context
        context = self.get_correlation_context(correlation_id)
        if not context:
            logger.warning(f"No context found for correlation: {correlation_id}")
            return

        # Extract analysis results
        # correlations = message.correlations
        # anomalies = message.anomalies
        # patterns = message.patterns

        # Send to Narrative Agent for report generation
        # narrative_request = messages_pb2.NarrativeRequest()
        # narrative_request.metadata.CopyFrom(create_metadata(self.agent_name, correlation_id))
        # narrative_request.analysis_results.CopyFrom(message)
        # narrative_request.query = context["context"]["original_query"]

        # Publish narrative request
        # self.publish_event(
        #     message=narrative_request,
        #     routing_key="narrative.request",
        #     correlation_id=correlation_id,
        # )

        # Clean up correlation tracking
        self.clear_correlation(correlation_id)

        logger.info(f"Completed query processing: {correlation_id}")


class DataRetrievalAgent(BaseAgent):
    """
    Example Data Retrieval Agent implementation.
    
    Demonstrates:
    - Handling requests
    - Publishing responses
    - Error handling
    """

    def __init__(self, connection_pool: ConnectionPool):
        """
        Initialize Data Retrieval Agent

        Args:
            connection_pool: RabbitMQ connection pool
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name="data_retrieval_agent",
            exchange_name="chimera.events",
            routing_keys=["data.request"],
            prefetch_count=5,  # Can handle multiple requests in parallel
        )

    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        """Map routing keys to message classes"""
        from google.protobuf.message import Message
        return {
            "data.request": Message,
        }

    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """Route message to handler"""
        correlation_id = properties.get("correlation_id")

        if routing_key == "data.request":
            self._handle_data_request(message, correlation_id)
        else:
            logger.warning(f"Unhandled routing key: {routing_key}")

    def _handle_data_request(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """
        Handle data retrieval request.

        Args:
            message: DataRetrievalRequest message
            correlation_id: Correlation ID from request
        """
        logger.info(f"Processing data request: {correlation_id}")

        try:
            # Retrieve data from sources
            # sources = message.sources
            # time_range = message.time_range
            # metrics = message.metrics

            # data_points = []
            # for source in sources:
            #     if source == "blockchain":
            #         data_points.extend(self._fetch_blockchain_data(...))
            #     elif source == "exchange":
            #         data_points.extend(self._fetch_exchange_data(...))

            # Build response
            # response = messages_pb2.DataRetrievalResponse()
            # response.metadata.CopyFrom(create_metadata(self.agent_name, correlation_id))
            # response.data.extend(data_points)
            # response.success = True

            # Publish response
            # self.publish_response(
            #     message=response,
            #     routing_key="data.response",
            #     correlation_id=correlation_id,
            # )

            logger.info(f"Completed data retrieval: {correlation_id}")

        except Exception as e:
            logger.error(f"Error retrieving data: {e}", exc_info=True)
            
            # Publish error response
            # error_response = messages_pb2.DataRetrievalResponse()
            # error_response.metadata.CopyFrom(create_metadata(self.agent_name, correlation_id))
            # error_response.success = False
            # error_response.error_message = str(e)

            # self.publish_response(
            #     message=error_response,
            #     routing_key="data.response",
            #     correlation_id=correlation_id,
            # )


def main():
    """Main entry point for running example agents"""
    import sys
    
    # Load configuration
    config = load_config()

    # Create connection pool
    connection_pool = ConnectionPool(config.rabbitmq)

    # Determine which agent to run
    agent_type = sys.argv[1] if len(sys.argv) > 1 else "query"

    try:
        if agent_type == "query":
            agent = QueryAgent(connection_pool)
            logger.info("Starting Query Agent...")
        elif agent_type == "data":
            agent = DataRetrievalAgent(connection_pool)
            logger.info("Starting Data Retrieval Agent...")
        else:
            logger.error(f"Unknown agent type: {agent_type}")
            sys.exit(1)

        # Start consuming messages
        agent.start_consuming()

    except KeyboardInterrupt:
        logger.info("Shutting down agent...")
    finally:
        connection_pool.close()


if __name__ == "__main__":
    main()

