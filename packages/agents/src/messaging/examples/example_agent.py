"""Example agent implementation demonstrating publisher and subscriber usage"""
import logging
from typing import Dict, Any, Type
from google.protobuf.message import Message as ProtoMessage

from ..connection import ConnectionPool
from ..publisher import EventPublisher
from ..subscriber import EventSubscriber
from ...config import load_config

# Note: Import generated protobuf messages after running proto generation
# from ..generated import messages_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleAgent(EventSubscriber):
    """Example agent that subscribes to events and publishes responses"""

    def __init__(self, connection_pool: ConnectionPool):
        """
        Initialize example agent

        Args:
            connection_pool: RabbitMQ connection pool
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name="example_agent",
            exchange_name="chimera.events",
            routing_keys=["query.request", "data.request"],
            prefetch_count=1,
        )

        # Create publisher for sending responses
        self.publisher = EventPublisher(
            connection_pool=connection_pool,
            agent_name="example_agent",
            exchange_name="chimera.events",
        )

    def get_message_class(self, routing_key: str) -> Type[ProtoMessage]:
        """
        Get message class based on routing key

        Args:
            routing_key: Routing key of the message

        Returns:
            Protocol Buffer message class
        """
        # Map routing keys to message classes
        # This would use the generated protobuf classes
        # routing_key_map = {
        #     "query.request": messages_pb2.QueryRequest,
        #     "data.request": messages_pb2.DataRetrievalRequest,
        # }
        # return routing_key_map.get(routing_key, messages_pb2.ErrorResponse)
        
        # Placeholder for demonstration
        from google.protobuf.message import Message
        return Message

    def handle_message(
        self, message: ProtoMessage, properties: Dict[str, Any]
    ) -> None:
        """
        Handle received message

        Args:
            message: Deserialized Protocol Buffer message
            properties: Message properties
        """
        routing_key = properties.get("routing_key")
        correlation_id = properties.get("correlation_id")

        logger.info(
            f"Processing message with routing key {routing_key}, "
            f"correlation_id: {correlation_id}"
        )

        # Process message based on routing key
        if routing_key == "query.request":
            self._handle_query_request(message, correlation_id)
        elif routing_key == "data.request":
            self._handle_data_request(message, correlation_id)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")

    def _handle_query_request(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """Handle query request"""
        logger.info("Handling query request")
        
        # Process the query
        # ... agent logic here ...
        
        # Publish response
        # response = messages_pb2.QueryResponse()
        # response.metadata.CopyFrom(create_metadata("example_agent", correlation_id))
        # self.publisher.publish(response, "query.response", correlation_id)

    def _handle_data_request(
        self, message: ProtoMessage, correlation_id: str
    ) -> None:
        """Handle data retrieval request"""
        logger.info("Handling data request")
        
        # Retrieve data
        # ... agent logic here ...
        
        # Publish response
        # response = messages_pb2.DataRetrievalResponse()
        # response.metadata.CopyFrom(create_metadata("example_agent", correlation_id))
        # self.publisher.publish(response, "data.response", correlation_id)

    def close(self) -> None:
        """Close agent resources"""
        super().close()
        self.publisher.close()


def main():
    """Main entry point for example agent"""
    # Load configuration
    config = load_config()

    # Create connection pool
    connection_pool = ConnectionPool(config.rabbitmq)

    try:
        # Create and start agent
        agent = ExampleAgent(connection_pool)
        logger.info("Starting example agent...")
        agent.start_consuming()

    except KeyboardInterrupt:
        logger.info("Shutting down example agent...")
    finally:
        connection_pool.close()


if __name__ == "__main__":
    main()
