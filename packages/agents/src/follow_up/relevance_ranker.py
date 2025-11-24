"""Relevance ranking for question suggestions."""
import logging
from typing import List
from .question_generator import Suggestion

logger = logging.getLogger(__name__)


class RelevanceRanker:
    """Ranks question suggestions by relevance."""

    def rank_suggestions(
        self,
        suggestions: List[Suggestion],
        session_history: List[str],
        data_availability: Dict[str, bool],
    ) -> List[Suggestion]:
        """
        Rank suggestions by relevance.

        Args:
            suggestions: Question suggestions
            session_history: Previous queries
            data_availability: Map of question to data availability

        Returns:
            Ranked suggestions
        """
        # Filter out questions similar to history
        filtered = self._filter_duplicates(suggestions, session_history)

        # Update data availability
        for suggestion in filtered:
            suggestion.data_available = data_availability.get(
                suggestion.question, True
            )

        # Sort by priority and data availability
        ranked = sorted(
            filtered,
            key=lambda s: (
                not s.data_available,  # Available first
                s.priority,  # Then by priority
            ),
        )

        return ranked[:5]  # Return top 5

    def _filter_duplicates(
        self, suggestions: List[Suggestion], history: List[str]
    ) -> List[Suggestion]:
        """Filter out questions similar to history."""
        filtered = []
        for suggestion in suggestions:
            # Simple similarity check (would use embeddings in production)
            is_duplicate = any(
                self._similar(suggestion.question, hq) for hq in history
            )
            if not is_duplicate:
                filtered.append(suggestion)
        return filtered

    def _similar(self, q1: str, q2: str) -> bool:
        """Check if two questions are similar."""
        # Simple word overlap check
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > 0.5

