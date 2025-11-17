"""Channel management utilities for RabbitMQ"""
import logging
from typing import Optional, Dict
from contextlib import contextmanager
import pika
from pika.channel import Channel
from pika.exceptions import AMQPChannelError

from .connection import ConnectionPool

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages RabbitMQ channels with automatic recovery"""

    def __init__(self, connection_pool: ConnectionPool):
        """
        Initialize channel manager

        Args:
            connection_pool: Connection pool to use for creating channels
        """
        self.connection_pool = connection_pool
        self._channels: Dict[str, Channel] = {}

    def get_channel(self, channel_id: str = "default") -> Channel:
        """
        Get or create a channel

        Args:
            channel_id: Identifier for the channel

        Returns:
            Active RabbitMQ channel

        Raises:
            AMQPChannelError: If channel creation fails
        """
        # Check if we have an existing open channel
        if channel_id in self._channels:
            channel = self._channels[channel_id]
            if channel.is_open:
                return channel
            else:
                logger.warning(f"Channel {channel_id} is closed, creating new one")
                del self._channels[channel_id]

        # Create new channel
        try:
            connection = self.connection_pool.get_connection()
            channel = connection.channel()
            self._channels[channel_id] = channel
            logger.info(f"Created new channel: {channel_id}")
            return channel

        except Exception as e:
            logger.error(f"Failed to create channel {channel_id}: {e}")
            raise AMQPChannelError(f"Could not create channel: {e}")

    def close_channel(self, channel_id: str = "default") -> None:
        """
        Close a specific channel

        Args:
            channel_id: Identifier for the channel to close
        """
        if channel_id in self._channels:
            channel = self._channels[channel_id]
            try:
                if channel.is_open:
                    logger.info(f"Closing channel: {channel_id}")
                    channel.close()
            except Exception as e:
                logger.error(f"Error closing channel {channel_id}: {e}")
            finally:
                del self._channels[channel_id]

    def close_all_channels(self) -> None:
        """Close all managed channels"""
        channel_ids = list(self._channels.keys())
        for channel_id in channel_ids:
            self.close_channel(channel_id)

    @contextmanager
    def channel_context(self, channel_id: str = "default"):
        """
        Context manager for channel usage

        Args:
            channel_id: Identifier for the channel

        Yields:
            Active RabbitMQ channel

        Example:
            with channel_manager.channel_context("my_channel") as channel:
                channel.basic_publish(...)
        """
        channel = self.get_channel(channel_id)
        try:
            yield channel
        except Exception as e:
            logger.error(f"Error in channel context {channel_id}: {e}")
            # Close and remove the channel on error
            self.close_channel(channel_id)
            raise

    def declare_exchange(
        self,
        channel: Channel,
        exchange_name: str,
        exchange_type: str = "topic",
        durable: bool = True,
    ) -> None:
        """
        Declare an exchange

        Args:
            channel: Channel to use for declaration
            exchange_name: Name of the exchange
            exchange_type: Type of exchange (direct, topic, fanout, headers)
            durable: Whether the exchange survives broker restart
        """
        try:
            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable,
            )
            logger.info(f"Declared exchange: {exchange_name} (type: {exchange_type})")
        except Exception as e:
            logger.error(f"Failed to declare exchange {exchange_name}: {e}")
            raise

    def declare_queue(
        self,
        channel: Channel,
        queue_name: str,
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
        arguments: Optional[Dict] = None,
    ) -> pika.frame.Method:
        """
        Declare a queue

        Args:
            channel: Channel to use for declaration
            queue_name: Name of the queue
            durable: Whether the queue survives broker restart
            exclusive: Whether the queue is exclusive to this connection
            auto_delete: Whether the queue is deleted when last consumer unsubscribes
            arguments: Additional queue arguments (e.g., TTL, dead letter exchange)

        Returns:
            Queue declaration result
        """
        try:
            result = channel.queue_declare(
                queue=queue_name,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                arguments=arguments or {},
            )
            logger.info(f"Declared queue: {queue_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {e}")
            raise

    def bind_queue(
        self,
        channel: Channel,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
    ) -> None:
        """
        Bind a queue to an exchange with a routing key

        Args:
            channel: Channel to use for binding
            queue_name: Name of the queue
            exchange_name: Name of the exchange
            routing_key: Routing key pattern
        """
        try:
            channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key,
            )
            logger.info(
                f"Bound queue {queue_name} to exchange {exchange_name} "
                f"with routing key {routing_key}"
            )
        except Exception as e:
            logger.error(
                f"Failed to bind queue {queue_name} to exchange {exchange_name}: {e}"
            )
            raise

    def __enter__(self) -> "ChannelManager":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close_all_channels()
