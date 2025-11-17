"""Event publisher for sending messages to RabbitMQ"""
import logging
from typing import Optional, Dict, Any
import pika
from google.protobuf.message import Message as ProtoMessage

from .connection import ConnectionPool
from .channel import ChannelManager
from .messages import serialize_message, create_metadata

logger = logging.getLogger(__name__)


class EventPublisher:
    """Base class for publishing events to the message bus"""

    def __init__(
        self,
        connection_pool: ConnectionPool,
        agent_name: str,
        exchange_name: str = "chimera.events",
        exchange_type: str = "topic",
    ):
        """
        Initialize event publisher

        Args:
            connection_pool: Connection pool for RabbitMQ
            agent_name: Name of the agent publishing events
            exchange_name: Name of the exchange to publish to
            exchange_type: Type of exchange (topic, direct, fanout)
        """
        self.connection_pool = connection_pool
        self.agent_name = agent_name
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.channel_manager = ChannelManager(connection_pool)
        self._setup_exchange()

    def _setup_exchange(self) -> None:
        """Declare the exchange"""
        try:
            channel = self.channel_manager.get_channel("publisher")
            self.channel_manager.declare_exchange(
                channel=channel,
                exchange_name=self.exchange_name,
                exchange_type=self.exchange_type,
                durable=True,
            )
        except Exception as e:
            logger.error(f"Failed to setup exchange: {e}")
            raise

    def publish(
        self,
        message: ProtoMessage,
        routing_key: str,
        correlation_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish a message to the exchange

        Args:
            message: Protocol Buffer message to publish
            routing_key: Routing key for message routing
            correlation_id: Optional correlation ID for request tracking
            properties: Optional additional message properties

        Raises:
            Exception: If publishing fails
        """
        try:
            channel = self.channel_manager.get_channel("publisher")

            # Serialize message
            body = serialize_message(message)

            # Build message properties
            msg_properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type="application/x-protobuf",
                correlation_id=correlation_id,
                app_id=self.agent_name,
                timestamp=int(pika.spec.BASIC_CLASS),
            )

            # Add custom properties if provided
            if properties:
                for key, value in properties.items():
                    if hasattr(msg_properties, key):
                        setattr(msg_properties, key, value)

            # Publish message
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=body,
                properties=msg_properties,
            )

            logger.info(
                f"Published message to {self.exchange_name} "
                f"with routing key {routing_key}"
            )

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    def publish_with_reply(
        self,
        message: ProtoMessage,
        routing_key: str,
        reply_queue: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish a message expecting a reply

        Args:
            message: Protocol Buffer message to publish
            routing_key: Routing key for message routing
            reply_queue: Queue name for replies
            correlation_id: Optional correlation ID for request tracking
        """
        properties = {"reply_to": reply_queue}
        self.publish(
            message=message,
            routing_key=routing_key,
            correlation_id=correlation_id,
            properties=properties,
        )

    def close(self) -> None:
        """Close publisher resources"""
        self.channel_manager.close_all_channels()

    def __enter__(self) -> "EventPublisher":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()
