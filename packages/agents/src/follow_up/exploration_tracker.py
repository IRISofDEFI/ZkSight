"""Exploration path tracking."""
import logging
from typing import List, Dict, Any, Set
import redis
from ..config import AgentConfig

logger = logging.getLogger(__name__)


class ExplorationTracker:
    """Tracks exploration paths and query history."""

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize exploration tracker.

        Args:
            redis_client: Redis client for storage
        """
        self.redis = redis_client

    def add_query(self, session_id: str, query: str) -> None:
        """
        Add query to session history.

        Args:
            session_id: Session identifier
            query: Query text
        """
        key = f"followup:history:{session_id}"
        self.redis.lpush(key, query)
        self.redis.ltrim(key, 0, 49)  # Keep last 50 queries
        self.redis.expire(key, 3600 * 24)  # Expire after 24 hours

    def get_history(self, session_id: str) -> List[str]:
        """
        Get query history for session.

        Args:
            session_id: Session identifier

        Returns:
            List of previous queries
        """
        key = f"followup:history:{session_id}"
        queries = self.redis.lrange(key, 0, -1)
        return [q.decode() if isinstance(q, bytes) else q for q in queries]

    def get_explored_dimensions(self, session_id: str) -> Set[str]:
        """
        Get explored data dimensions.

        Args:
            session_id: Session identifier

        Returns:
            Set of explored dimension names
        """
        key = f"followup:dimensions:{session_id}"
        dimensions = self.redis.smembers(key)
        return {
            d.decode() if isinstance(d, bytes) else d for d in dimensions
        }

    def mark_dimension_explored(self, session_id: str, dimension: str) -> None:
        """
        Mark dimension as explored.

        Args:
            session_id: Session identifier
            dimension: Dimension name
        """
        key = f"followup:dimensions:{session_id}"
        self.redis.sadd(key, dimension)
        self.redis.expire(key, 3600 * 24)

