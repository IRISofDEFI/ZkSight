"""Audit trail storage."""
import logging
from typing import List, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from ..config import AgentConfig
from .claim_extractor import Claim
from .verification_manager import VerifiedClaim

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Audit log entry."""

    claim_id: str
    timestamp: int
    action: str
    result: str
    details: Dict[str, str]


class AuditLogger:
    """Logs verification checks to MongoDB."""

    def __init__(self, config: AgentConfig):
        """
        Initialize audit logger.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.client = MongoClient(config.mongodb.uri)
        self.db = self.client[config.mongodb.database]
        self.audit_collection = self.db["fact_check_audit"]

        # Create indexes
        self.audit_collection.create_index("claim_id")
        self.audit_collection.create_index("timestamp")

    def log_verification(
        self, claim: Claim, verified_claim: VerifiedClaim
    ) -> str:
        """
        Log verification check.

        Args:
            claim: Original claim
            verified_claim: Verification result

        Returns:
            Audit entry ID
        """
        entry = AuditEntry(
            claim_id=claim.id,
            timestamp=int(datetime.now().timestamp() * 1000),
            action="verify",
            result="verified" if verified_claim.verified else "failed",
            details={
                "confidence": str(verified_claim.confidence),
                "sources": ",".join(verified_claim.sources),
                "metric": claim.metric,
                "value": str(claim.value),
            },
        )

        doc = {
            "claim_id": entry.claim_id,
            "timestamp": datetime.fromtimestamp(entry.timestamp / 1000),
            "action": entry.action,
            "result": entry.result,
            "details": entry.details,
        }

        result = self.audit_collection.insert_one(doc)
        logger.info(f"Logged audit entry: {result.inserted_id}")
        return str(result.inserted_id)

    def log_conflict(self, conflict: Any) -> str:
        """
        Log conflict detection.

        Args:
            conflict: Data conflict

        Returns:
            Audit entry ID
        """
        entry = AuditEntry(
            claim_id=conflict.claim.id,
            timestamp=int(datetime.now().timestamp() * 1000),
            action="detect_conflict",
            result="conflict_detected",
            details={
                "resolution": conflict.resolution,
                "sources": ",".join([s.source for s in conflict.sources]),
            },
        )

        doc = {
            "claim_id": entry.claim_id,
            "timestamp": datetime.fromtimestamp(entry.timestamp / 1000),
            "action": entry.action,
            "result": entry.result,
            "details": entry.details,
        }

        result = self.audit_collection.insert_one(doc)
        return str(result.inserted_id)

    def get_audit_trail(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Get audit trail for a claim.

        Args:
            claim_id: Claim identifier

        Returns:
            List of audit entries
        """
        entries = self.audit_collection.find({"claim_id": claim_id}).sort(
            "timestamp", 1
        )
        return [
            {
                "_id": str(e["_id"]),
                "claim_id": e["claim_id"],
                "timestamp": int(e["timestamp"].timestamp() * 1000),
                "action": e["action"],
                "result": e["result"],
                "details": e["details"],
            }
            for e in entries
        ]

