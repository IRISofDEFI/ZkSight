"""Query clarification engine for handling ambiguous queries"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClarificationEngine:
    """
    Detects ambiguity in queries and generates clarification questions.
    
    Handles missing entities, ambiguous references, and unclear intents.
    """

    def __init__(self):
        """Initialize clarification engine"""
        pass

    def check_for_ambiguity(
        self,
        query: str,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if query needs clarification.

        Args:
            query: Original query text
            intent: Classified intent
            entities: Extracted entities
            context: Conversation context

        Returns:
            Dictionary with clarification_needed flag and questions
        """
        clarification_questions = []
        ambiguity_reasons = []

        # Check for missing time range
        if self._needs_time_range_clarification(intent, entities, context):
            question = self._generate_time_range_question(intent)
            if question:
                clarification_questions.append(question)
                ambiguity_reasons.append("missing_time_range")

        # Check for missing metrics
        if self._needs_metric_clarification(intent, entities, context):
            question = self._generate_metric_question(intent)
            if question:
                clarification_questions.append(question)
                ambiguity_reasons.append("missing_metrics")

        # Check for ambiguous comparisons
        if self._needs_comparison_clarification(intent, entities):
            question = self._generate_comparison_question(entities)
            if question:
                clarification_questions.append(question)
                ambiguity_reasons.append("ambiguous_comparison")

        # Check for low confidence intent
        if self._needs_intent_clarification(intent):
            question = self._generate_intent_question(query, intent)
            if question:
                clarification_questions.append(question)
                ambiguity_reasons.append("unclear_intent")

        # Check for ambiguous entity references
        if self._needs_entity_clarification(entities):
            question = self._generate_entity_question(entities)
            if question:
                clarification_questions.append(question)
                ambiguity_reasons.append("ambiguous_entity")

        return {
            "clarification_needed": len(clarification_questions) > 0,
            "questions": clarification_questions,
            "reasons": ambiguity_reasons,
        }

    def _needs_time_range_clarification(
        self,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """Check if time range needs clarification"""
        # Check if intent has time range
        if intent.get("time_range"):
            return False

        # Check if entities contain time information
        has_time_entity = any(
            e.get("entity_type") in ["TIME_RANGE", "DATE"]
            for e in entities
        )
        if has_time_entity:
            return False

        # Check if context has time range
        if context.get("time_range_context"):
            return False

        # For trend analysis and anomaly detection, time range is critical
        intent_type = intent.get("intent_type")
        if intent_type and intent_type.value in [
            "INTENT_TREND_ANALYSIS",
            "INTENT_ANOMALY_DETECTION"
        ]:
            return True

        return False

    def _needs_metric_clarification(
        self,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """Check if metrics need clarification"""
        # Check if intent has metrics
        if intent.get("metrics"):
            return False

        # Check if entities contain metrics
        has_metric_entity = any(
            e.get("entity_type") == "METRIC"
            for e in entities
        )
        if has_metric_entity:
            return False

        # Check if context has metrics
        if context.get("metric_context"):
            return False

        # All intents need at least one metric
        return True

    def _needs_comparison_clarification(
        self,
        intent: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> bool:
        """Check if comparison needs clarification"""
        intent_type = intent.get("intent_type")
        if not intent_type or intent_type.value != "INTENT_COMPARISON":
            return False

        # For comparison, we need at least 2 metrics or 2 time periods
        metrics = [e for e in entities if e.get("entity_type") == "METRIC"]
        time_entities = [
            e for e in entities 
            if e.get("entity_type") in ["TIME_RANGE", "DATE"]
        ]

        # Need either multiple metrics or multiple time periods
        if len(metrics) < 2 and len(time_entities) < 2:
            return True

        return False

    def _needs_intent_clarification(self, intent: Dict[str, Any]) -> bool:
        """Check if intent needs clarification"""
        confidence = intent.get("confidence", 0.0)
        intent_type = intent.get("intent_type")

        # If confidence is low or intent is unknown
        if confidence < 0.5 or (intent_type and intent_type.value == "INTENT_UNKNOWN"):
            return True

        return False

    def _needs_entity_clarification(self, entities: List[Dict[str, Any]]) -> bool:
        """Check if entities need clarification"""
        # Check for entities with low confidence
        for entity in entities:
            if entity.get("confidence", 1.0) < 0.6:
                return True

        return False

    def _generate_time_range_question(self, intent: Dict[str, Any]) -> Optional[str]:
        """Generate question about time range"""
        intent_type = intent.get("intent_type")
        
        if intent_type and intent_type.value == "INTENT_TREND_ANALYSIS":
            return (
                "What time period would you like to analyze? "
                "(e.g., last 7 days, last month, this year)"
            )
        elif intent_type and intent_type.value == "INTENT_ANOMALY_DETECTION":
            return (
                "What time period should I check for anomalies? "
                "(e.g., last 24 hours, last week)"
            )
        else:
            return (
                "What time period are you interested in? "
                "(e.g., today, last week, last month)"
            )

    def _generate_metric_question(self, intent: Dict[str, Any]) -> Optional[str]:
        """Generate question about metrics"""
        # Provide common metric options
        common_metrics = [
            "shielded transactions",
            "price",
            "trading volume",
            "hash rate",
            "social sentiment"
        ]

        return (
            f"Which metric would you like to analyze? "
            f"Some options: {', '.join(common_metrics)}"
        )

    def _generate_comparison_question(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate question about comparison"""
        metrics = [
            e.get("canonical_name", e.get("value"))
            for e in entities 
            if e.get("entity_type") == "METRIC"
        ]

        if len(metrics) == 1:
            return (
                f"What would you like to compare {metrics[0]} against? "
                f"(e.g., another metric, a previous time period)"
            )
        else:
            return (
                "What would you like to compare? "
                "(e.g., two metrics, two time periods)"
            )

    def _generate_intent_question(
        self, 
        query: str, 
        intent: Dict[str, Any]
    ) -> Optional[str]:
        """Generate question about intent"""
        return (
            "I'm not sure what you're looking for. Are you trying to:\n"
            "- Analyze trends over time\n"
            "- Detect anomalies or unusual activity\n"
            "- Compare different metrics or time periods\n"
            "- Understand why something happened"
        )

    def _generate_entity_question(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate question about ambiguous entities"""
        low_confidence_entities = [
            e for e in entities 
            if e.get("confidence", 1.0) < 0.6
        ]

        if not low_confidence_entities:
            return None

        entity = low_confidence_entities[0]
        entity_value = entity.get("value")

        return f"Did you mean '{entity_value}'? Please clarify."

    def parse_clarification_response(
        self,
        response: str,
        original_question: str
    ) -> Dict[str, Any]:
        """
        Parse user's response to clarification question.

        Args:
            response: User's clarification response
            original_question: The clarification question asked

        Returns:
            Dictionary with parsed information
        """
        response_lower = response.lower().strip()

        # Detect if this is a time range response
        if "time period" in original_question.lower():
            return {
                "type": "time_range",
                "value": response,
            }

        # Detect if this is a metric response
        if "metric" in original_question.lower():
            return {
                "type": "metric",
                "value": response,
            }

        # Detect if this is an intent response
        if "trying to" in original_question.lower():
            intent_mapping = {
                "trend": "INTENT_TREND_ANALYSIS",
                "anomal": "INTENT_ANOMALY_DETECTION",
                "compare": "INTENT_COMPARISON",
                "why": "INTENT_EXPLANATION",
                "understand": "INTENT_EXPLANATION",
            }

            for keyword, intent_value in intent_mapping.items():
                if keyword in response_lower:
                    return {
                        "type": "intent",
                        "value": intent_value,
                    }

        # Generic response
        return {
            "type": "generic",
            "value": response,
        }

    def integrate_clarification(
        self,
        original_query: str,
        clarification_response: Dict[str, Any],
        entities: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate clarification response into query understanding.

        Args:
            original_query: Original query text
            clarification_response: Parsed clarification response
            entities: Original entities
            intent: Original intent

        Returns:
            Updated query understanding
        """
        response_type = clarification_response.get("type")
        response_value = clarification_response.get("value")

        updated_entities = entities.copy()
        updated_intent = intent.copy()

        if response_type == "time_range":
            # Add time range entity
            # This would need to be parsed through entity recognizer
            updated_entities.append({
                "entity_type": "TIME_RANGE",
                "value": response_value,
                "confidence": 1.0,
                "source": "clarification",
            })

        elif response_type == "metric":
            # Add metric entity
            updated_entities.append({
                "entity_type": "METRIC",
                "value": response_value,
                "confidence": 1.0,
                "source": "clarification",
            })

        elif response_type == "intent":
            # Update intent
            from .intent_classifier import IntentType
            updated_intent["intent_type"] = IntentType(response_value)
            updated_intent["confidence"] = 1.0

        return {
            "entities": updated_entities,
            "intent": updated_intent,
            "clarified": True,
        }
