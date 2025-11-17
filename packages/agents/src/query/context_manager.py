"""Conversation context management with Redis storage"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import redis

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context across multiple queries in a session.
    
    Stores context in Redis with TTL for automatic cleanup.
    """

    DEFAULT_TTL = 3600  # 1 hour in seconds

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl: int = DEFAULT_TTL,
        key_prefix: str = "chimera:context:"
    ):
        """
        Initialize context manager.

        Args:
            redis_client: Redis client instance
            ttl: Time-to-live for context entries in seconds
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.ttl = ttl
        self.key_prefix = key_prefix

    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self.key_prefix}{session_id}"

    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Context dictionary or None if not found
        """
        try:
            key = self._get_key(session_id)
            data = self.redis.get(key)
            
            if data:
                context = json.loads(data)
                logger.debug(f"Retrieved context for session {session_id}")
                return context
            
            logger.debug(f"No context found for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            return None

    def save_context(
        self, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Save conversation context for a session.

        Args:
            session_id: Session identifier
            context: Context dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(session_id)
            
            # Add timestamp
            context["last_updated"] = datetime.now().isoformat()
            
            # Serialize and save
            data = json.dumps(context)
            self.redis.setex(key, self.ttl, data)
            
            logger.debug(f"Saved context for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving context: {e}", exc_info=True)
            return False

    def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific fields in context.

        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        context = self.get_context(session_id) or {}
        context.update(updates)
        return self.save_context(session_id, context)

    def add_query_to_history(
        self,
        session_id: str,
        query: str,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> bool:
        """
        Add a query to the conversation history.

        Args:
            session_id: Session identifier
            query: Query text
            intent: Classified intent
            entities: Extracted entities

        Returns:
            True if successful, False otherwise
        """
        context = self.get_context(session_id) or {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "query_history": [],
        }

        # Add query to history
        query_entry = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "entities": entities,
        }
        
        context["query_history"].append(query_entry)
        
        # Keep only last 10 queries
        if len(context["query_history"]) > 10:
            context["query_history"] = context["query_history"][-10:]

        return self.save_context(session_id, context)

    def get_query_history(
        self, 
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get query history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of queries to return (most recent)

        Returns:
            List of query entries
        """
        context = self.get_context(session_id)
        if not context:
            return []

        history = context.get("query_history", [])
        
        if limit:
            return history[-limit:]
        
        return history

    def extract_context_for_query(
        self,
        session_id: str,
        current_query: str
    ) -> Dict[str, Any]:
        """
        Extract relevant context for the current query.

        Args:
            session_id: Session identifier
            current_query: Current query text

        Returns:
            Dictionary with relevant context information
        """
        context = self.get_context(session_id)
        if not context:
            return {}

        history = context.get("query_history", [])
        
        # Get last query for reference resolution
        last_query = history[-1] if history else None

        # Extract common entities from recent queries
        recent_entities = self._extract_common_entities(history[-3:])

        # Extract time range context
        time_range_context = self._extract_time_range_context(history[-3:])

        # Extract metric context
        metric_context = self._extract_metric_context(history[-3:])

        return {
            "last_query": last_query,
            "recent_entities": recent_entities,
            "time_range_context": time_range_context,
            "metric_context": metric_context,
            "query_count": len(history),
        }

    def merge_context_with_entities(
        self,
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Merge context information with extracted entities.

        Args:
            entities: Extracted entities from current query
            context: Context from previous queries

        Returns:
            Enhanced entity list with context
        """
        enhanced_entities = entities.copy()

        # If no time range in current query, use from context
        has_time_range = any(
            e.get("entity_type") in ["TIME_RANGE", "DATE"] 
            for e in entities
        )
        
        if not has_time_range and context.get("time_range_context"):
            enhanced_entities.append({
                "entity_type": "TIME_RANGE",
                "value": "from context",
                "confidence": 0.7,
                "resolved_range": context["time_range_context"],
                "source": "context",
            })

        # If no metrics in current query, use from context
        has_metrics = any(
            e.get("entity_type") == "METRIC" 
            for e in entities
        )
        
        if not has_metrics and context.get("metric_context"):
            for metric in context["metric_context"]:
                enhanced_entities.append({
                    "entity_type": "METRIC",
                    "value": metric,
                    "confidence": 0.6,
                    "canonical_name": metric,
                    "source": "context",
                })

        return enhanced_entities

    def _extract_common_entities(
        self, 
        history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract entities that appear in multiple recent queries"""
        entity_counts: Dict[str, int] = {}
        entity_data: Dict[str, Dict[str, Any]] = {}

        for query_entry in history:
            entities = query_entry.get("entities", [])
            for entity in entities:
                key = f"{entity.get('entity_type')}:{entity.get('value')}"
                entity_counts[key] = entity_counts.get(key, 0) + 1
                entity_data[key] = entity

        # Return entities that appear more than once
        common = [
            entity_data[key]
            for key, count in entity_counts.items()
            if count > 1
        ]

        return common

    def _extract_time_range_context(
        self, 
        history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, int]]:
        """Extract most recent time range from history"""
        for query_entry in reversed(history):
            intent = query_entry.get("intent", {})
            time_range = intent.get("time_range")
            if time_range:
                return time_range
        return None

    def _extract_metric_context(
        self, 
        history: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract metrics from recent queries"""
        metrics = []
        for query_entry in reversed(history):
            intent = query_entry.get("intent", {})
            query_metrics = intent.get("metrics", [])
            for metric in query_metrics:
                if metric not in metrics:
                    metrics.append(metric)
        return metrics

    def clear_context(self, session_id: str) -> bool:
        """
        Clear context for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(session_id)
            self.redis.delete(key)
            logger.debug(f"Cleared context for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing context: {e}", exc_info=True)
            return False

    def extend_ttl(self, session_id: str) -> bool:
        """
        Extend TTL for a session's context.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(session_id)
            self.redis.expire(key, self.ttl)
            logger.debug(f"Extended TTL for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error extending TTL: {e}", exc_info=True)
            return False
