"""Event subscriber for consuming messages from RabbitMQ"""
import logging
from typing import Callable, Optional, Dict, Any, Type
from abc import ABC, abstractmethod
import pika
from google.protobuf.message import Message as ProtoMessage

from .connection import ConnectionPool
from .channel import ChannelManager
from .messages import deserialize_message, extract_correlation_id

logger = logging.getLogger(__name__)


MessageHandler = Callable[[ProtoMessage, Dict[str, Any]], None]


class EventSubscriber(ABC):
    """Base class for subscribing to events from the message bus"""

    def __init__(
        self,
        connection_pool: ConnectionPool,
        agent_name: str,
        exchange_name: str = "chimera.events",
        queue_name: Optional[str] = None,
        routing_keys: Optional[list[str]] = None,
        prefetch_count: int = 1,
    ):
        """
        Initialize event subscriber

        Args:
            connection_pool: Connection pool for RabbitMQ
            agent_name: Name of the agent subscribing to events
            exchange_name: Name of the exchange to subscribe to
            queue_name: Name of the queue (defaults to agent_name)
            routing_keys: List of routing keys to bind (defaults to ["#"])
            prefetch_count: Number of messages to prefetch
        """
        self.connection_pool = connection_pool
        self.agent_name = agent_name
        self.exchange_name = exchange_name
        self.queue_name = queue_name or agent_name
        self.routing_keys = routing_keys or ["#"]
        self.prefetch_count = prefetch_count
        self.channel_manager = ChannelManager(connection_pool)
        self._consuming = False
        self._setup_queue()

    def _setup_queue(self) -> None:
        """Declare queue and bind to exchange"""
        try:
            channel = self.channel_manager.get_channel("subscriber")

            # Declare exchange
            self.channel_manager.declare_exchange(
                channel=channel,
                exchange_name=self.exchange_name,
                exchange_type="topic",
                durable=True,
            )

            # Declare queue with dead letter exchange
            dlx_args = {
                "x-dead-letter-exchange": f"{self.exchange_name}.dlx",
                "x-message-ttl": 86400000,  # 24 hours
            }

            self.channel_manager.declare_queue(
                channel=channel,
                queue_name=self.queue_name,
                durable=True,
                arguments=dlx_args,
            )

            # Declare dead letter queue
            dlq_name = f"{self.queue_name}.dlq"
            self.channel_manager.declare_exchange(
                channel=channel,
                exchange_name=f"{self.exchange_name}.dlx",
                exchange_type="topic",
                durable=True,
            )
            self.channel_manager.declare_queue(
                channel=channel,
                queue_name=dlq_name,
                durable=True,
            )

            # Bind dead letter queue
            for routing_key in self.routing_keys:
                self.channel_manager.bind_queue(
                    channel=channel,
                    queue_name=dlq_name,
                    exchange_name=f"{self.exchange_name}.dlx",
                    routing_key=routing_key,
                )

            # Bind main queue to exchange
            for routing_key in self.routing_keys:
                self.channel_manager.bind_queue(
                    channel=channel,
                    queue_name=self.queue_name,
                    exchange_name=self.exchange_name,
                    routing_key=routing_key,
                )

            # Set QoS
            channel.basic_qos(prefetch_count=self.prefetch_count)

            logger.info(
                f"Setup queue {self.queue_name} bound to {self.exchange_name} "
                f"with routing keys {self.routing_keys}"
            )

        except Exception as e:
            logger.error(f"Failed to setup queue: {e}")
            raise

    @abstractmethod
    def handle_message(
        self, message: ProtoMessage, properties: Dict[str, Any]
    ) -> None:
        """
        Handle received message (must be implemented by subclasses)

        Args:
            message: Deserialized Protocol Buffer message
            properties: Message properties (correlation_id, routing_key, etc.)
        """
        pass

    @abstractmethod
    def get_message_class(self, routing_key: str) -> Type[ProtoMessage]:
        """
        Get the Protocol Buffer message class for a routing key

        Args:
            routing_key: Routing key of the message

        Returns:
            Protocol Buffer message class
        """
        pass

    def _on_message(
        self,
        channel: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """
        Internal message callback

        Args:
            channel: Channel the message was received on
            method: Delivery method
            properties: Message properties
            body: Message body
        """
        try:
            # Extract properties
            msg_properties = {
                "routing_key": method.routing_key,
                "correlation_id": properties.correlation_id,
                "delivery_tag": method.delivery_tag,
                "app_id": properties.app_id,
            }

            logger.info(
                f"Received message with routing key {method.routing_key} "
                f"(correlation_id: {properties.correlation_id})"
            )

            # Get message class and deserialize
            message_class = self.get_message_class(method.routing_key)
            message = deserialize_message(body, message_class)

            # Handle message
            self.handle_message(message, msg_properties)

            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Acknowledged message {method.delivery_tag}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Reject and requeue message (will go to DLQ after retries)
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,  # Send to DLQ
            )

    def start_consuming(self) -> None:
        """Start consuming messages"""
        try:
            channel = self.channel_manager.get_channel("subscriber")
            channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False,
            )

            self._consuming = True
            logger.info(f"Started consuming from queue {self.queue_name}")
            channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            raise

    def stop_consuming(self) -> None:
        """Stop consuming messages"""
        if self._consuming:
            try:
                channel = self.channel_manager.get_channel("subscriber")
                channel.stop_consuming()
                self._consuming = False
                logger.info("Stopped consuming")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")

    def close(self) -> None:
        """Close subscriber resources"""
        self.stop_consuming()
        self.channel_manager.close_all_channels()

    def __enter__(self) -> "EventSubscriber":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()
