"""Claim extraction from narratives using NLP."""
import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """Extracted claim model."""

    id: str
    statement: str
    metric: str
    value: float
    time_range: Dict[str, int]


class ClaimExtractor:
    """Extracts factual claims from narrative text."""

    def extract_claims(self, report_text: str) -> List[Claim]:
        """
        Extract claims from report text.

        Args:
            report_text: Report text to analyze

        Returns:
            List of extracted claims
        """
        claims = []

        # Pattern for numeric claims (e.g., "price was $50.23")
        numeric_pattern = r"(\w+)\s+(?:was|is|reached|at)\s+([$]?)(\d+\.?\d*)"

        # Pattern for metric mentions
        metric_pattern = r"(shielded\s+transactions?|price|volume|hash\s+rate|difficulty)"

        # Find all numeric claims
        for match in re.finditer(numeric_pattern, report_text, re.IGNORECASE):
            metric = match.group(1)
            value_str = match.group(3)
            try:
                value = float(value_str)
                claim = Claim(
                    id=f"claim_{len(claims)}",
                    statement=match.group(0),
                    metric=metric,
                    value=value,
                    time_range={},
                )
                claims.append(claim)
            except ValueError:
                continue

        # Find metric mentions
        for match in re.finditer(metric_pattern, report_text, re.IGNORECASE):
            metric = match.group(1).lower().replace(" ", "_")
            # Try to find associated value nearby
            context = report_text[max(0, match.start() - 50) : match.end() + 50]
            value_match = re.search(r"(\d+\.?\d*)", context)
            if value_match:
                try:
                    value = float(value_match.group(1))
                    claim = Claim(
                        id=f"claim_{len(claims)}",
                        statement=context.strip(),
                        metric=metric,
                        value=value,
                        time_range={},
                    )
                    claims.append(claim)
                except ValueError:
                    continue

        logger.info(f"Extracted {len(claims)} claims from report")
        return claims

