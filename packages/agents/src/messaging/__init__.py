"""Message bus components for agent communication"""
from .connection import ConnectionPool, get_connection_pool
from .channel import ChannelManager
from .publisher import EventPublisher
from .subscriber import EventSubscriber
from .base_agent import BaseAgent
from .messages import (
    MessageBuilder,
    create_metadata,
    serialize_message,
    deserialize_message,
    extract_correlation_id,
    extract_message_id,
)

__all__ = [
    "ConnectionPool",
    "ChannelManager",
    "EventPublisher",
    "EventSubscriber",
    "BaseAgent",
    "MessageBuilder",
    "get_connection_pool",
    "create_metadata",
    "serialize_message",
    "deserialize_message",
    "extract_correlation_id",
    "extract_message_id",
]
