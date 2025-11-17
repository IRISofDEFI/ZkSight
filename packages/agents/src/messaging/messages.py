"""Message utilities and helpers for Protocol Buffer messages"""
import time
import uuid
from typing import Optional, Dict, Any
from google.protobuf.message import Message as ProtoMessage


def create_metadata(
    sender_agent: str,
    correlation_id: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create message metadata

    Args:
        sender_agent: Name of the agent sending the message
        correlation_id: Optional correlation ID for request tracking
        reply_to: Optional reply queue name

    Returns:
        Dictionary with metadata fields
    """
    return {
        "message_id": str(uuid.uuid4()),
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),  # milliseconds
        "sender_agent": sender_agent,
        "reply_to": reply_to or "",
    }


def serialize_message(message: ProtoMessage) -> bytes:
    """
    Serialize a Protocol Buffer message to bytes

    Args:
        message: Protocol Buffer message instance

    Returns:
        Serialized message bytes
    """
    return message.SerializeToString()


def deserialize_message(data: bytes, message_class: type) -> ProtoMessage:
    """
    Deserialize bytes to a Protocol Buffer message

    Args:
        data: Serialized message bytes
        message_class: Protocol Buffer message class

    Returns:
        Deserialized message instance
    """
    message = message_class()
    message.ParseFromString(data)
    return message


class MessageBuilder:
    """Helper class for building Protocol Buffer messages"""

    def __init__(self, sender_agent: str):
        """
        Initialize message builder

        Args:
            sender_agent: Name of the agent building messages
        """
        self.sender_agent = sender_agent

    def create_metadata_dict(
        self,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create metadata dictionary"""
        return create_metadata(
            sender_agent=self.sender_agent,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )


def extract_correlation_id(message: ProtoMessage) -> Optional[str]:
    """
    Extract correlation ID from a message

    Args:
        message: Protocol Buffer message with metadata field

    Returns:
        Correlation ID if present, None otherwise
    """
    if hasattr(message, "metadata") and hasattr(message.metadata, "correlation_id"):
        return message.metadata.correlation_id
    return None


def extract_message_id(message: ProtoMessage) -> Optional[str]:
    """
    Extract message ID from a message

    Args:
        message: Protocol Buffer message with metadata field

    Returns:
        Message ID if present, None otherwise
    """
    if hasattr(message, "metadata") and hasattr(message.metadata, "message_id"):
        return message.metadata.message_id
    return None
