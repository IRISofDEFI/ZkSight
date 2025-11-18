"""Report storage and export."""
import logging
import json
from typing import Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from ..config import AgentConfig
from .report_builder import Report

logger = logging.getLogger(__name__)


class NarrativeStorage:
    """Stores reports in MongoDB with TTL."""

    def __init__(self, config: AgentConfig):
        """
        Initialize narrative storage.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.client = MongoClient(config.mongodb.uri)
        self.db = self.client[config.mongodb.database]
        self.reports_collection = self.db["reports"]

        # Create TTL index (reports expire after 90 days)
        self.reports_collection.create_index(
            "created_at", expireAfterSeconds=90 * 24 * 60 * 60
        )

    def store_report(
        self, report: Report, report_id: str, user_id: Optional[str] = None
    ) -> str:
        """
        Store report in MongoDB.

        Args:
            report: Report to store
            report_id: Unique report identifier
            user_id: Optional user identifier

        Returns:
            Stored report ID
        """
        doc = {
            "_id": report_id,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                }
                for s in report.sections
            ],
            "created_at": datetime.fromtimestamp(report.created_at / 1000),
            "user_id": user_id,
        }

        self.reports_collection.insert_one(doc)
        logger.info(f"Stored report: {report_id}")
        return report_id

    def get_report(self, report_id: str) -> Optional[dict]:
        """
        Retrieve report from MongoDB.

        Args:
            report_id: Report identifier

        Returns:
            Report document or None
        """
        doc = self.reports_collection.find_one({"_id": report_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            doc["created_at"] = int(doc["created_at"].timestamp() * 1000)
        return doc

    def export_json(self, report: Report) -> str:
        """
        Export report as JSON.

        Args:
            report: Report to export

        Returns:
            JSON string
        """
        return json.dumps(
            {
                "title": report.title,
                "executive_summary": report.executive_summary,
                "sections": [
                    {
                        "title": s.title,
                        "content": s.content,
                        "order": s.order,
                    }
                    for s in report.sections
                ],
                "created_at": report.created_at,
            },
            indent=2,
        )

    def export_html(self, report: Report) -> str:
        """
        Export report as HTML.

        Args:
            report: Report to export

        Returns:
            HTML string
        """
        sections_html = "\n".join(
            [
                f"""
                <section>
                    <h2>{s.title}</h2>
                    <p>{s.content.replace(chr(10), '<br>')}</p>
                </section>
                """
                for s in sorted(report.sections, key=lambda x: x.order)
            ]
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                section {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>{report.title}</h1>
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <p>{report.executive_summary.replace(chr(10), '<br>')}</p>
            </div>
            {sections_html}
        </body>
        </html>
        """

