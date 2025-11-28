"""Base agent class combining publisher and subscriber functionality"""
import logging
import uuid
from typing import Dict, Any, Type, Optional, List
from abc import ABC, abstractmethod
from google.protobuf.message import Message as ProtoMessage

from .connection import ConnectionPool
from .publisher import EventPublisher
from .subscriber import EventSubscriber
from .messages import create_metadata

# Import tracing utilities
try:
    from ..tracing import (
        get_tracer,
        inject_trace_context,
        extract_trace_context,
        trace_message_processing,
        set_span_attribute,
        add_span_event,
        set_span_error,
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseAgent(EventSubscriber):
    """
    Base class for all agents in the Chimera system.
    
    Provides:
    - Event subscription with automatic routing
    - Event publishing with correlation ID tracking
    - Dead letter queue handling
    - Message routing based on routing keys
    - Request-response pattern support
    """

    def __init__(
        self,
        connection_pool: ConnectionPool,
        agent_name: str,
        exchange_name: str = "chimera.events",
        routing_keys: Optional[List[str]] = None,
        prefetch_count: int = 1,
    ):
        """
        Initialize base agent

        Args:
            connection_pool: RabbitMQ connection pool
            agent_name: Unique name for this agent
            exchange_name: Exchange to publish/subscribe to
            routing_keys: List of routing key patterns to subscribe to
            prefetch_count: Number of messages to prefetch
        """
        # Initialize subscriber
        super().__init__(
            connection_pool=connection_pool,
            agent_name=agent_name,
            exchange_name=exchange_name,
            queue_name=agent_name,
            routing_keys=routing_keys or [f"{agent_name}.#"],
            prefetch_count=prefetch_count,
        )

        # Initialize publisher
        self.publisher = EventPublisher(
            connection_pool=connection_pool,
            agent_name=agent_name,
            exchange_name=exchange_name,
        )

        # Track correlation IDs for request-response patterns
        self._correlation_map: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Initialized {agent_name} agent")

    def get_message_class(self, routing_key: str) -> Type[ProtoMessage]:
        """
        Get Protocol Buffer message class for a routing key.
        
        Must be implemented by subclasses to map routing keys to message types.

        Args:
            routing_key: Routing key of the incoming message

        Returns:
            Protocol Buffer message class
        """
        message_map = self.get_routing_key_map()
        message_class = message_map.get(routing_key)
        
        if message_class is None:
            logger.warning(
                f"No message class found for routing key: {routing_key}"
            )
            # Return a generic message class or raise an error
            raise ValueError(f"Unknown routing key: {routing_key}")
        
        return message_class

    @abstractmethod
    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        """
        Get mapping of routing keys to Protocol Buffer message classes.
        
        Must be implemented by subclasses.

        Returns:
            Dictionary mapping routing keys to message classes
        """
        pass

    def handle_message(
        self, message: ProtoMessage, properties: Dict[str, Any]
    ) -> None:
        """
        Handle received message by routing to appropriate handler.

        Args:
            message: Deserialized Protocol Buffer message
            properties: Message properties (routing_key, correlation_id, etc.)
        """
        routing_key = properties.get("routing_key", "")
        correlation_id = properties.get("correlation_id")

        logger.info(
            f"[{self.agent_name}] Received message: "
            f"routing_key={routing_key}, correlation_id={correlation_id}"
        )

        # Extract trace context from message headers if available
        if TRACING_AVAILABLE and "headers" in properties:
            try:
                extract_trace_context(properties["headers"])
            except Exception as e:
                logger.debug(f"Could not extract trace context: {e}")

        # Create span for message processing
        if TRACING_AVAILABLE:
            try:
                with trace_message_processing(routing_key, correlation_id or ""):
                    set_span_attribute("agent.name", self.agent_name)
                    set_span_attribute("message.routing_key", routing_key)
                    if correlation_id:
                        set_span_attribute("message.correlation_id", correlation_id)
                    
                    add_span_event("message.received")
                    
                    try:
                        # Route message to handler
                        self.route_message(message, routing_key, properties)
                        add_span_event("message.processed")
                    except Exception as e:
                        set_span_error(e)
                        logger.error(
                            f"[{self.agent_name}] Error handling message: {e}",
                            exc_info=True
                        )
                        raise
            except Exception as e:
                # If tracing itself fails, still process the message
                logger.debug(f"Tracing error (continuing): {e}")
                try:
                    self.route_message(message, routing_key, properties)
                except Exception as e:
                    logger.error(
                        f"[{self.agent_name}] Error handling message: {e}",
                        exc_info=True
                    )
                    raise
        else:
            try:
                # Route message to handler
                self.route_message(message, routing_key, properties)
            except Exception as e:
                logger.error(
                    f"[{self.agent_name}] Error handling message: {e}",
                    exc_info=True
                )
                # Error will cause message to be rejected and sent to DLQ
                raise

    @abstractmethod
    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Route message to appropriate handler based on routing key.
        
        Must be implemented by subclasses.

        Args:
            message: Deserialized Protocol Buffer message
            routing_key: Routing key of the message
            properties: Message properties
        """
        pass

    def publish_event(
        self,
        message: ProtoMessage,
        routing_key: str,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Publish an event to the message bus.

        Args:
            message: Protocol Buffer message to publish
            routing_key: Routing key for message routing
            correlation_id: Optional correlation ID (generated if not provided)

        Returns:
            Correlation ID used for the message
        """
        # Generate correlation ID if not provided
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        # Inject trace context into message headers if tracing is available
        headers = {}
        if TRACING_AVAILABLE:
            try:
                inject_trace_context(headers)
                set_span_attribute("message.published", routing_key)
                add_span_event("message.publish", {
                    "routing_key": routing_key,
                    "correlation_id": correlation_id,
                })
            except Exception as e:
                logger.debug(f"Could not inject trace context: {e}")

        # Publish message
        self.publisher.publish(
            message=message,
            routing_key=routing_key,
            correlation_id=correlation_id,
            headers=headers if headers else None,
        )

        logger.debug(
            f"[{self.agent_name}] Published event: "
            f"routing_key={routing_key}, correlation_id={correlation_id}"
        )

        return correlation_id

    def publish_request(
        self,
        message: ProtoMessage,
        routing_key: str,
        reply_routing_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Publish a request expecting a response.

        Args:
            message: Protocol Buffer message to publish
            routing_key: Routing key for the request
            reply_routing_key: Routing key pattern for the expected reply
            context: Optional context data to store with correlation ID

        Returns:
            Correlation ID for tracking the request
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Store context for correlation tracking
        self._correlation_map[correlation_id] = {
            "request_routing_key": routing_key,
            "reply_routing_key": reply_routing_key,
            "context": context or {},
            "timestamp": self._get_timestamp(),
        }

        # Publish request
        self.publisher.publish(
            message=message,
            routing_key=routing_key,
            correlation_id=correlation_id,
        )

        logger.debug(
            f"[{self.agent_name}] Published request: "
            f"routing_key={routing_key}, correlation_id={correlation_id}"
        )

        return correlation_id

    def publish_response(
        self,
        message: ProtoMessage,
        routing_key: str,
        correlation_id: str,
    ) -> None:
        """
        Publish a response to a previous request.

        Args:
            message: Protocol Buffer message to publish
            routing_key: Routing key for the response
            correlation_id: Correlation ID from the original request
        """
        self.publisher.publish(
            message=message,
            routing_key=routing_key,
            correlation_id=correlation_id,
        )

        logger.debug(
            f"[{self.agent_name}] Published response: "
            f"routing_key={routing_key}, correlation_id={correlation_id}"
        )

    def get_correlation_context(
        self, correlation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get stored context for a correlation ID.

        Args:
            correlation_id: Correlation ID to lookup

        Returns:
            Context dictionary if found, None otherwise
        """
        return self._correlation_map.get(correlation_id)

    def clear_correlation(self, correlation_id: str) -> None:
        """
        Clear stored context for a correlation ID.

        Args:
            correlation_id: Correlation ID to clear
        """
        if correlation_id in self._correlation_map:
            del self._correlation_map[correlation_id]
            logger.debug(
                f"[{self.agent_name}] Cleared correlation: {correlation_id}"
            )

    def cleanup_old_correlations(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old correlation entries.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            Number of entries cleaned up
        """
        current_time = self._get_timestamp()
        cutoff_time = current_time - (max_age_seconds * 1000)
        
        old_ids = [
            corr_id
            for corr_id, data in self._correlation_map.items()
            if data.get("timestamp", 0) < cutoff_time
        ]

        for corr_id in old_ids:
            del self._correlation_map[corr_id]

        if old_ids:
            logger.info(
                f"[{self.agent_name}] Cleaned up {len(old_ids)} "
                f"old correlation entries"
            )

        return len(old_ids)

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        import time
        return int(time.time() * 1000)

    def close(self) -> None:
        """Close agent resources"""
        logger.info(f"[{self.agent_name}] Closing agent...")
        
        # Close publisher
        self.publisher.close()
        
        # Close subscriber (parent class)
        super().close()
        
        # Clear correlation map
        self._correlation_map.clear()

    def __enter__(self) -> "BaseAgent":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()

