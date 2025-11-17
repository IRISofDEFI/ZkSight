"""Intent classification for query understanding"""
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
import re

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Query intent types"""
    UNKNOWN = "INTENT_UNKNOWN"
    TREND_ANALYSIS = "INTENT_TREND_ANALYSIS"
    ANOMALY_DETECTION = "INTENT_ANOMALY_DETECTION"
    COMPARISON = "INTENT_COMPARISON"
    EXPLANATION = "INTENT_EXPLANATION"


class IntentClassifier:
    """
    Classifies query intent using pattern matching and keyword analysis.
    
    Can be extended with BERT-based classification for improved accuracy.
    """

    # Intent patterns - keywords and phrases that indicate specific intents
    INTENT_PATTERNS = {
        IntentType.TREND_ANALYSIS: {
            "keywords": [
                "trend", "trending", "over time", "growth", "decline",
                "increase", "decrease", "change", "evolution", "progression",
                "historical", "history", "pattern", "moving average",
                "how has", "how did", "what happened", "track"
            ],
            "question_words": ["how", "what"],
            "verbs": ["grow", "change", "evolve", "move", "shift", "trend"],
        },
        IntentType.ANOMALY_DETECTION: {
            "keywords": [
                "anomaly", "anomalies", "unusual", "abnormal", "outlier",
                "spike", "drop", "sudden", "unexpected", "irregular",
                "strange", "odd", "deviation", "alert", "warning",
                "significant change", "dramatic"
            ],
            "question_words": ["what", "when", "why"],
            "verbs": ["spike", "drop", "jump", "plunge", "surge"],
        },
        IntentType.COMPARISON: {
            "keywords": [
                "compare", "comparison", "versus", "vs", "against",
                "difference", "between", "relative to", "compared to",
                "higher", "lower", "more", "less", "better", "worse",
                "correlation", "relationship", "than"
            ],
            "question_words": ["how", "what", "which"],
            "verbs": ["compare", "differ", "relate", "correlate"],
        },
        IntentType.EXPLANATION: {
            "keywords": [
                "why", "because", "reason", "cause", "explain", "explanation",
                "what caused", "what led to", "what drove", "factor",
                "influence", "impact", "effect", "result", "due to",
                "behind", "responsible for"
            ],
            "question_words": ["why", "how", "what"],
            "verbs": ["cause", "lead", "drive", "influence", "affect", "result"],
        },
    }

    def __init__(self, use_transformer: bool = False, model_name: Optional[str] = None):
        """
        Initialize intent classifier.

        Args:
            use_transformer: Whether to use transformer-based classification
            model_name: Name of transformer model (if use_transformer=True)
        """
        self.use_transformer = use_transformer
        self.model_name = model_name
        self.model = None
        self.tokenizer = None

        if use_transformer:
            self._load_transformer_model()

    def _load_transformer_model(self) -> None:
        """Load transformer model for intent classification"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            model_name = self.model_name or "bert-base-uncased"
            logger.info(f"Loading transformer model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(IntentType)
            )
            
            logger.info("Transformer model loaded successfully")
        except Exception as e:
            logger.warning(
                f"Failed to load transformer model: {e}. "
                f"Falling back to pattern-based classification."
            )
            self.use_transformer = False

    def classify(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify query intent.

        Args:
            text: Query text
            entities: Extracted entities from the query

        Returns:
            Dictionary with intent type, confidence, and supporting evidence
        """
        if self.use_transformer and self.model:
            return self._classify_with_transformer(text)
        else:
            return self._classify_with_patterns(text, entities)

    def _classify_with_patterns(
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify intent using pattern matching.

        Args:
            text: Query text
            entities: Extracted entities

        Returns:
            Classification result with intent, confidence, and evidence
        """
        text_lower = text.lower()
        scores = {intent: 0.0 for intent in IntentType}

        # Score each intent based on pattern matches
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            score = 0.0
            matched_keywords = []

            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            # Check question words
            for qword in patterns["question_words"]:
                if text_lower.startswith(qword):
                    score += 0.5

            # Check verbs
            for verb in patterns["verbs"]:
                if re.search(r"\b" + verb + r"\w*\b", text_lower):
                    score += 0.8

            scores[intent_type] = score

        # Determine primary intent
        max_score = max(scores.values())
        
        if max_score == 0:
            primary_intent = IntentType.UNKNOWN
            confidence = 0.0
        else:
            primary_intent = max(scores, key=scores.get)
            # Normalize confidence to 0-1 range
            confidence = min(max_score / 3.0, 1.0)  # 3 matches = 100% confidence

        # Extract time range from entities
        time_range = self._extract_time_range(entities)

        # Extract metrics from entities
        metrics = self._extract_metrics(entities)

        return {
            "intent_type": primary_intent,
            "confidence": confidence,
            "scores": {intent.value: score for intent, score in scores.items()},
            "time_range": time_range,
            "metrics": metrics,
        }

    def _classify_with_transformer(self, text: str) -> Dict[str, Any]:
        """
        Classify intent using transformer model.

        Args:
            text: Query text

        Returns:
            Classification result
        """
        import torch
        
        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=1)

        # Get predicted class and confidence
        predicted_idx = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][predicted_idx].item()

        # Map index to intent type
        intent_types = list(IntentType)
        primary_intent = intent_types[predicted_idx]

        return {
            "intent_type": primary_intent,
            "confidence": confidence,
            "scores": {
                intent.value: probabilities[0][i].item()
                for i, intent in enumerate(intent_types)
            },
            "time_range": None,
            "metrics": [],
        }

    def _extract_time_range(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, int]]:
        """Extract time range from entities"""
        for entity in entities:
            if entity.get("entity_type") == "TIME_RANGE":
                return entity.get("resolved_range")
            elif entity.get("entity_type") == "DATE":
                timestamp = entity.get("resolved_timestamp")
                if timestamp:
                    # Create a single-day range
                    return {
                        "start_timestamp": timestamp,
                        "end_timestamp": timestamp + (24 * 60 * 60 * 1000),
                    }
        return None

    def _extract_metrics(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Extract metric names from entities"""
        metrics = []
        for entity in entities:
            if entity.get("entity_type") == "METRIC":
                canonical_name = entity.get("canonical_name")
                if canonical_name and canonical_name not in metrics:
                    metrics.append(canonical_name)
        return metrics

    def get_secondary_intents(
        self, 
        classification: Dict[str, Any],
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get secondary intents that also match the query.

        Args:
            classification: Primary classification result
            threshold: Minimum score threshold for secondary intents

        Returns:
            List of secondary intent dictionaries
        """
        secondary = []
        primary_intent = classification["intent_type"]
        scores = classification.get("scores", {})

        for intent_value, score in scores.items():
            intent_type = IntentType(intent_value)
            if intent_type != primary_intent and score >= threshold:
                secondary.append({
                    "intent_type": intent_type,
                    "score": score,
                })

        # Sort by score descending
        secondary.sort(key=lambda x: x["score"], reverse=True)
        return secondary
