"""RabbitMQ connection pool with retry logic and exponential backoff"""
import logging
import time
from typing import Optional
import pika
from pika.adapters.blocking_connection import BlockingConnection
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from ..config import RabbitMQConfig

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages RabbitMQ connections with retry logic and exponential backoff"""

    def __init__(
        self,
        config: RabbitMQConfig,
        max_retries: int = 5,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ):
        """
        Initialize connection pool

        Args:
            config: RabbitMQ configuration
            max_retries: Maximum number of connection retry attempts
            initial_retry_delay: Initial delay between retries in seconds
            max_retry_delay: Maximum delay between retries in seconds
        """
        self.config = config
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self._connection: Optional[BlockingConnection] = None
        self._connection_params = self._build_connection_params()

    def _build_connection_params(self) -> pika.ConnectionParameters:
        """Build connection parameters from config"""
        credentials = pika.PlainCredentials(
            username=self.config.username,
            password=self.config.password,
        )

        return pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            virtual_host=self.config.vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.initial_retry_delay * (2**attempt)
        return min(delay, self.max_retry_delay)

    def connect(self) -> BlockingConnection:
        """
        Establish connection to RabbitMQ with retry logic

        Returns:
            Active RabbitMQ connection

        Raises:
            AMQPConnectionError: If connection fails after all retries
        """
        if self._connection and self._connection.is_open:
            return self._connection

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Attempting to connect to RabbitMQ at "
                    f"{self.config.host}:{self.config.port} (attempt {attempt + 1}/{self.max_retries})"
                )
                self._connection = pika.BlockingConnection(self._connection_params)
                logger.info("Successfully connected to RabbitMQ")
                return self._connection

            except (AMQPConnectionError, AMQPChannelError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        f"Failed to connect to RabbitMQ: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Failed to connect to RabbitMQ after {self.max_retries} attempts"
                    )

        raise AMQPConnectionError(
            f"Could not connect to RabbitMQ after {self.max_retries} attempts: {last_error}"
        )

    def get_connection(self) -> BlockingConnection:
        """
        Get active connection, reconnecting if necessary

        Returns:
            Active RabbitMQ connection
        """
        if not self._connection or not self._connection.is_open:
            return self.connect()
        return self._connection

    def close(self) -> None:
        """Close the connection gracefully"""
        if self._connection and self._connection.is_open:
            try:
                logger.info("Closing RabbitMQ connection")
                self._connection.close()
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")
            finally:
                self._connection = None

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self._connection is not None and self._connection.is_open

    def __enter__(self) -> "ConnectionPool":
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()


# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None


def get_connection_pool(config: Optional[RabbitMQConfig] = None) -> ConnectionPool:
    """
    Get or create global connection pool instance

    Args:
        config: RabbitMQ configuration (required on first call)

    Returns:
        Global connection pool instance

    Raises:
        ValueError: If config is not provided on first call
    """
    global _connection_pool

    if _connection_pool is None:
        if config is None:
            raise ValueError("Config must be provided when creating connection pool")
        _connection_pool = ConnectionPool(config)

    return _connection_pool
