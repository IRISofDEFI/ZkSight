"""Entity recognizer for dates, metrics, and Zcash-specific terms"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class EntityRecognizer:
    """
    Recognizes entities specific to Zcash analytics queries.
    
    Extracts:
    - Temporal entities (dates, time ranges)
    - Metric names
    - Zcash-specific terms (transaction types, address types)
    """

    # Zcash-specific metrics
    ZCASH_METRICS = {
        "shielded_transactions": ["shielded transaction", "shielded tx", "private transaction"],
        "transparent_transactions": ["transparent transaction", "transparent tx", "public transaction"],
        "shielded_pool_size": ["shielded pool", "pool size", "anonymity set"],
        "block_height": ["block height", "block number", "blocks"],
        "hash_rate": ["hash rate", "hashrate", "mining power"],
        "difficulty": ["difficulty", "mining difficulty"],
        "transaction_fees": ["fees", "transaction fee", "tx fee"],
        "transaction_volume": ["transaction volume", "tx volume", "volume"],
        "price": ["price", "zcash price", "zec price"],
        "trading_volume": ["trading volume", "market volume"],
        "market_cap": ["market cap", "market capitalization"],
        "social_sentiment": ["sentiment", "social sentiment", "community sentiment"],
        "developer_activity": ["developer activity", "github activity", "commits"],
    }

    # Zcash-specific terms
    ZCASH_TERMS = {
        "address_types": ["sprout", "sapling", "orchard", "transparent", "shielded"],
        "transaction_types": ["shielded", "transparent", "private", "public"],
        "networks": ["mainnet", "testnet"],
    }

    # Temporal patterns
    TEMPORAL_PATTERNS = {
        "relative_day": r"\b(today|yesterday|tomorrow)\b",
        "relative_week": r"\b(this week|last week|next week)\b",
        "relative_month": r"\b(this month|last month|next month)\b",
        "relative_year": r"\b(this year|last year|next year)\b",
        "last_n_days": r"\blast\s+(\d+)\s+days?\b",
        "last_n_weeks": r"\blast\s+(\d+)\s+weeks?\b",
        "last_n_months": r"\blast\s+(\d+)\s+months?\b",
        "past_n_hours": r"\bpast\s+(\d+)\s+hours?\b",
    }

    def __init__(self):
        """Initialize entity recognizer"""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency"""
        self.compiled_patterns = {
            key: re.compile(pattern, re.IGNORECASE)
            for key, pattern in self.TEMPORAL_PATTERNS.items()
        }

    def recognize_entities(
        self, 
        text: str, 
        doc: Optional[Doc] = None
    ) -> List[Dict[str, Any]]:
        """
        Recognize all entities in text.

        Args:
            text: Input query text
            doc: Optional spaCy Doc object for additional context

        Returns:
            List of recognized entities with type, value, and confidence
        """
        entities = []

        # Extract temporal entities
        entities.extend(self._extract_temporal_entities(text))

        # Extract metric entities
        entities.extend(self._extract_metric_entities(text))

        # Extract Zcash-specific terms
        entities.extend(self._extract_zcash_terms(text))

        # Extract numeric values
        entities.extend(self._extract_numeric_entities(text))

        # Use spaCy entities if available
        if doc:
            entities.extend(self._extract_spacy_entities(doc))

        return entities

    def _extract_temporal_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract temporal entities (dates, time ranges)"""
        entities = []
        text_lower = text.lower()

        # Check relative temporal patterns
        for pattern_name, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text_lower)
            for match in matches:
                time_range = self._resolve_temporal_pattern(
                    pattern_name, 
                    match.group(0),
                    match.group(1) if match.groups() else None
                )
                if time_range:
                    entities.append({
                        "entity_type": "TIME_RANGE",
                        "value": match.group(0),
                        "confidence": 0.9,
                        "resolved_range": time_range,
                    })

        # Try to parse absolute dates
        date_entities = self._extract_absolute_dates(text)
        entities.extend(date_entities)

        return entities

    def _resolve_temporal_pattern(
        self, 
        pattern_name: str, 
        matched_text: str,
        numeric_value: Optional[str] = None
    ) -> Optional[Dict[str, int]]:
        """Resolve temporal pattern to timestamp range"""
        now = datetime.now()
        start_time = None
        end_time = now

        if pattern_name == "relative_day":
            if "today" in matched_text:
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif "yesterday" in matched_text:
                start_time = (now - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

        elif pattern_name == "relative_week":
            if "this week" in matched_text:
                start_time = now - timedelta(days=now.weekday())
            elif "last week" in matched_text:
                start_time = now - timedelta(days=now.weekday() + 7)
                end_time = now - timedelta(days=now.weekday())

        elif pattern_name == "relative_month":
            if "this month" in matched_text:
                start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif "last month" in matched_text:
                first_of_this_month = now.replace(day=1)
                end_time = first_of_this_month
                start_time = (first_of_this_month - timedelta(days=1)).replace(day=1)

        elif pattern_name == "last_n_days" and numeric_value:
            days = int(numeric_value)
            start_time = now - timedelta(days=days)

        elif pattern_name == "last_n_weeks" and numeric_value:
            weeks = int(numeric_value)
            start_time = now - timedelta(weeks=weeks)

        elif pattern_name == "last_n_months" and numeric_value:
            months = int(numeric_value)
            start_time = now - timedelta(days=months * 30)  # Approximate

        elif pattern_name == "past_n_hours" and numeric_value:
            hours = int(numeric_value)
            start_time = now - timedelta(hours=hours)

        if start_time:
            return {
                "start_timestamp": int(start_time.timestamp() * 1000),
                "end_timestamp": int(end_time.timestamp() * 1000),
            }

        return None

    def _extract_absolute_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract absolute date mentions"""
        entities = []
        
        # Common date patterns
        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
            r"\b\d{2}/\d{2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    parsed_date = date_parser.parse(match.group(0))
                    entities.append({
                        "entity_type": "DATE",
                        "value": match.group(0),
                        "confidence": 0.85,
                        "resolved_timestamp": int(parsed_date.timestamp() * 1000),
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse date '{match.group(0)}': {e}")

        return entities

    def _extract_metric_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract metric names from text"""
        entities = []
        text_lower = text.lower()

        for metric_name, variations in self.ZCASH_METRICS.items():
            for variation in variations:
                if variation in text_lower:
                    entities.append({
                        "entity_type": "METRIC",
                        "value": variation,
                        "confidence": 0.9,
                        "canonical_name": metric_name,
                    })
                    break  # Only match once per metric

        return entities

    def _extract_zcash_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract Zcash-specific terminology"""
        entities = []
        text_lower = text.lower()

        for term_category, terms in self.ZCASH_TERMS.items():
            for term in terms:
                if term in text_lower:
                    entities.append({
                        "entity_type": "ZCASH_TERM",
                        "value": term,
                        "confidence": 0.95,
                        "category": term_category,
                    })

        return entities

    def _extract_numeric_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract numeric values and percentages"""
        entities = []

        # Extract percentages
        percentage_pattern = r"\b(\d+(?:\.\d+)?)\s*%"
        for match in re.finditer(percentage_pattern, text):
            entities.append({
                "entity_type": "PERCENTAGE",
                "value": match.group(0),
                "confidence": 0.95,
                "numeric_value": float(match.group(1)),
            })

        # Extract numbers with units
        number_pattern = r"\b(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand|k|m|b)?\b"
        for match in re.finditer(number_pattern, text, re.IGNORECASE):
            value = match.group(1).replace(",", "")
            unit = match.group(2)
            
            numeric_value = float(value)
            if unit:
                unit_lower = unit.lower()
                if unit_lower in ["k", "thousand"]:
                    numeric_value *= 1000
                elif unit_lower in ["m", "million"]:
                    numeric_value *= 1000000
                elif unit_lower in ["b", "billion"]:
                    numeric_value *= 1000000000

            entities.append({
                "entity_type": "NUMBER",
                "value": match.group(0),
                "confidence": 0.9,
                "numeric_value": numeric_value,
            })

        return entities

    def _extract_spacy_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Extract entities from spaCy Doc"""
        entities = []
        
        for ent in doc.ents:
            # Only include relevant entity types
            if ent.label_ in ["DATE", "TIME", "MONEY", "PERCENT", "CARDINAL", "ORDINAL"]:
                entities.append({
                    "entity_type": ent.label_,
                    "value": ent.text,
                    "confidence": 0.8,
                    "source": "spacy",
                })

        return entities
