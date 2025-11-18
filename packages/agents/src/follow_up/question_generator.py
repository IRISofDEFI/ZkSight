"""Question generation using LLM."""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from ..config import AgentConfig
from ..narrative.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """Follow-up question suggestion."""

    question: str
    rationale: str
    priority: int
    data_available: bool
    estimated_complexity: str


class QuestionGenerator:
    """Generates contextual follow-up questions."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize question generator.

        Args:
            llm_client: LLM client for question generation
        """
        self.llm_client = llm_client

    async def generate_questions(
        self,
        original_query: str,
        analysis_results: Any,
        report: Any,
        session_history: List[str],
    ) -> List[Suggestion]:
        """
        Generate follow-up questions.

        Args:
            original_query: Original user query
            analysis_results: Analysis results
            report: Generated report
            session_history: Previous queries in session

        Returns:
            List of question suggestions
        """
        # Build context for question generation
        context = self._build_context(original_query, analysis_results, report)

        # Generate questions using LLM
        prompt = f"""Based on this analysis, generate 5 relevant follow-up questions.

Original Query: {original_query}

Analysis Summary:
- Statistics analyzed: {len(getattr(analysis_results, 'statistics', []))}
- Anomalies detected: {len(getattr(analysis_results, 'anomalies', []))}
- Correlations found: {len(getattr(analysis_results, 'correlations', []))}

Previous questions asked: {', '.join(session_history[-3:]) if session_history else 'None'}

Generate questions that:
1. Explore deeper into the findings
2. Compare different time periods or metrics
3. Ask about causes or implications
4. Request predictive analysis
5. Explore related dimensions

Format each question on a new line.
"""

        response = await self.llm_client.generate_text(prompt, max_tokens=500)
        questions = [q.strip() for q in response.split("\n") if q.strip()]

        # Convert to suggestions
        suggestions = []
        for i, question in enumerate(questions[:5]):
            suggestions.append(
                Suggestion(
                    question=question,
                    rationale=f"Generated based on analysis findings",
                    priority=i + 1,
                    data_available=True,  # Would check actual data availability
                    estimated_complexity="medium",
                )
            )

        return suggestions

    def _build_context(
        self, query: str, analysis_results: Any, report: Any
    ) -> str:
        """Build context string for question generation."""
        context_parts = [f"Original query: {query}"]

        if analysis_results:
            if hasattr(analysis_results, "anomalies") and analysis_results.anomalies:
                context_parts.append(
                    f"Anomalies: {len(analysis_results.anomalies)} detected"
                )
            if hasattr(analysis_results, "correlations") and analysis_results.correlations:
                context_parts.append(
                    f"Correlations: {len(analysis_results.correlations)} found"
                )

        if report:
            summary = getattr(report, "executive_summary", "")
            if summary:
                context_parts.append(f"Summary: {summary[:200]}...")

        return "\n".join(context_parts)

