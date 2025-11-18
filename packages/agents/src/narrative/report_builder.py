"""Report structure generation."""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..analysis.models import AnalysisResultBundle

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """Report section model."""

    title: str
    content: str
    order: int


@dataclass
class Report:
    """Report model."""

    title: str
    executive_summary: str
    sections: List[ReportSection]
    created_at: int


class ReportBuilder:
    """Builds structured reports from analysis results."""

    def __init__(self, llm_client: Any):
        """
        Initialize report builder.

        Args:
            llm_client: LLM client for text generation
        """
        self.llm_client = llm_client

    async def build_report(
        self,
        analysis_results: AnalysisResultBundle,
        original_query: str,
        user_expertise_level: str = "intermediate",
    ) -> Report:
        """
        Build complete report from analysis results.

        Args:
            analysis_results: Analysis results bundle
            original_query: Original user query
            user_expertise_level: User expertise level (beginner/intermediate/expert)

        Returns:
            Complete report
        """
        import time

        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            analysis_results, original_query, user_expertise_level
        )

        # Generate sections
        sections = []
        sections.append(
            ReportSection(
                title="Key Findings",
                content=await self._generate_findings(
                    analysis_results, user_expertise_level
                ),
                order=1,
            )
        )

        if analysis_results.anomalies:
            sections.append(
                ReportSection(
                    title="Anomalies Detected",
                    content=await self._generate_anomalies_section(
                        analysis_results, user_expertise_level
                    ),
                    order=2,
                )
            )

        if analysis_results.correlations:
            sections.append(
                ReportSection(
                    title="Correlations",
                    content=await self._generate_correlations_section(
                        analysis_results, user_expertise_level
                    ),
                    order=3,
                )
            )

        if analysis_results.patterns:
            sections.append(
                ReportSection(
                    title="Patterns Identified",
                    content=await self._generate_patterns_section(
                        analysis_results, user_expertise_level
                    ),
                    order=4,
                )
            )

        sections.append(
            ReportSection(
                title="Methodology",
                content=self._generate_methodology_section(analysis_results),
                order=5,
            )
        )

        return Report(
            title=f"Analysis Report: {original_query}",
            executive_summary=executive_summary,
            sections=sections,
            created_at=int(time.time() * 1000),
        )

    async def _generate_executive_summary(
        self,
        analysis_results: AnalysisResultBundle,
        query: str,
        expertise_level: str,
    ) -> str:
        """Generate executive summary."""
        prompt = f"""Generate an executive summary for the following analysis results.

Query: {query}
User Expertise Level: {expertise_level}

Analysis Results:
- Statistics: {len(analysis_results.statistics)} metrics analyzed
- Anomalies: {len(analysis_results.anomalies)} detected
- Correlations: {len(analysis_results.correlations)} found
- Patterns: {len(analysis_results.patterns)} identified

Write a concise executive summary (2-3 paragraphs) suitable for {expertise_level} level users.
"""
        return await self.llm_client.generate_text(prompt, max_tokens=500)

    async def _generate_findings(
        self, analysis_results: AnalysisResultBundle, expertise_level: str
    ) -> str:
        """Generate key findings section."""
        findings = []
        for stat in analysis_results.statistics[:5]:
            findings.append(
                f"- {stat.metric}: mean={stat.mean:.2f}, std={stat.std_dev:.2f}"
            )

        prompt = f"""Based on these statistics, generate key findings:

{chr(10).join(findings)}

Write findings suitable for {expertise_level} level users.
"""
        return await self.llm_client.generate_text(prompt, max_tokens=800)

    async def _generate_anomalies_section(
        self, analysis_results: AnalysisResultBundle, expertise_level: str
    ) -> str:
        """Generate anomalies section."""
        anomalies_text = "\n".join(
            [
                f"- {a.metric} at {a.timestamp}: value={a.value:.2f}, "
                f"expected={a.expected_value:.2f}, severity={a.severity}"
                for a in analysis_results.anomalies[:10]
            ]
        )

        prompt = f"""Explain these anomalies in user-friendly language:

{anomalies_text}

Write for {expertise_level} level users.
"""
        return await self.llm_client.generate_text(prompt, max_tokens=1000)

    async def _generate_correlations_section(
        self, analysis_results: AnalysisResultBundle, expertise_level: str
    ) -> str:
        """Generate correlations section."""
        corr_text = "\n".join(
            [
                f"- {c.metric1} vs {c.metric2}: "
                f"coefficient={c.coefficient:.3f}, "
                f"significant={c.significant}"
                for c in analysis_results.correlations[:10]
            ]
        )

        prompt = f"""Explain these correlations:

{corr_text}

Write for {expertise_level} level users.
"""
        return await self.llm_client.generate_text(prompt, max_tokens=1000)

    async def _generate_patterns_section(
        self, analysis_results: AnalysisResultBundle, expertise_level: str
    ) -> str:
        """Generate patterns section."""
        patterns_text = "\n".join(
            [
                f"- {p.pattern_type} in {p.metric}: {p.description}, "
                f"confidence={p.confidence:.2f}"
                for p in analysis_results.patterns[:10]
            ]
        )

        prompt = f"""Explain these patterns:

{patterns_text}

Write for {expertise_level} level users.
"""
        return await self.llm_client.generate_text(prompt, max_tokens=1000)

    def _generate_methodology_section(
        self, analysis_results: AnalysisResultBundle
    ) -> str:
        """Generate methodology section."""
        methods = []
        if analysis_results.anomalies:
            methods.append("Z-score based anomaly detection")
        if analysis_results.correlations:
            methods.append("Pearson correlation analysis")
        if analysis_results.patterns:
            methods.append("Moving average and pattern recognition")

        return f"""This analysis used the following methods:
{chr(10).join(f'- {m}' for m in methods)}

Statistical significance was tested using p-values with a threshold of 0.05.
"""

