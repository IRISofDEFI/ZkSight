"""Conflict detection and resolution."""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from .claim_extractor import Claim
from .verification_manager import Evidence

logger = logging.getLogger(__name__)


@dataclass
class ConflictSource:
    """Source with conflicting value."""

    source: str
    value: float
    difference: float


@dataclass
class DataConflict:
    """Detected data conflict."""

    claim: Claim
    sources: List[ConflictSource]
    resolution: str


class ConflictDetector:
    """Detects conflicts across data sources."""

    def detect_conflicts(
        self, claims: List[Claim], evidence_list: List[List[Evidence]]
    ) -> List[DataConflict]:
        """
        Detect conflicts across data sources.

        Args:
            claims: Claims to check
            evidence_list: Evidence for each claim

        Returns:
            List of detected conflicts
        """
        conflicts = []

        for claim, evidence in zip(claims, evidence_list):
            if len(evidence) < 2:
                continue  # Need at least 2 sources to detect conflict

            # Extract values from different sources
            source_values = {}
            for ev in evidence:
                try:
                    # Parse value from evidence (simplified)
                    value = self._extract_value_from_evidence(ev)
                    if value is not None:
                        source_values[ev.source] = value
                except Exception as e:
                    logger.warning(f"Error extracting value from evidence: {e}")

            # Check for conflicts (values differ by more than 5%)
            if len(source_values) >= 2:
                values = list(source_values.values())
                max_val = max(values)
                min_val = min(values)
                diff_percent = ((max_val - min_val) / max_val) * 100 if max_val > 0 else 0

                if diff_percent > 5.0:  # 5% threshold
                    conflict_sources = [
                        ConflictSource(
                            source=source,
                            value=value,
                            difference=abs(value - claim.value),
                        )
                        for source, value in source_values.items()
                    ]

                    resolution = self._generate_resolution(claim, conflict_sources)

                    conflicts.append(
                        DataConflict(
                            claim=claim,
                            sources=conflict_sources,
                            resolution=resolution,
                        )
                    )

        return conflicts

    def _extract_value_from_evidence(self, evidence: Evidence) -> Optional[float]:
        """Extract numeric value from evidence."""
        import json

        try:
            data = json.loads(evidence.data_json)
            if isinstance(data, dict):
                # Try common keys
                for key in ["value", "price", "amount", "volume"]:
                    if key in data:
                        return float(data[key])
            elif isinstance(data, (int, float)):
                return float(data)
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        return None

    def _generate_resolution(
        self, claim: Claim, conflict_sources: List[ConflictSource]
    ) -> str:
        """Generate conflict resolution text."""
        sources_text = ", ".join([f"{s.source}={s.value}" for s in conflict_sources])
        return f"Conflict detected: {sources_text}. Using average value."

