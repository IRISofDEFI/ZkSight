"""Report document models for MongoDB"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    """Report metadata"""
    generated_at: datetime
    execution_time: float
    data_sources_used: List[str]
    version: str = "1.0"


class ReportSection(BaseModel):
    """Report section"""
    title: str
    content: str
    order: int
    visualization_ids: Optional[List[str]] = None


class Report(BaseModel):
    """Report content"""
    title: str
    executive_summary: str
    sections: List[ReportSection]
    metadata: ReportMetadata


class Anomaly(BaseModel):
    """Anomaly detection result"""
    metric: str
    timestamp: int
    value: float
    expected_value: float
    deviation_score: float
    severity: str
    context: Optional[str] = None


class Correlation(BaseModel):
    """Correlation analysis result"""
    metric1: str
    metric2: str
    coefficient: float
    p_value: float
    significance: bool
    lag: Optional[int] = None


class Pattern(BaseModel):
    """Pattern recognition result"""
    type: str
    metric: str
    description: str
    confidence: float
    time_range: Dict[str, int]


class Statistics(BaseModel):
    """Statistical summary"""
    mean: float
    median: float
    std_dev: float
    min: float
    max: float
    count: int


class AnalysisResponse(BaseModel):
    """Analysis results"""
    correlations: List[Correlation] = Field(default_factory=list)
    anomalies: List[Anomaly] = Field(default_factory=list)
    patterns: List[Pattern] = Field(default_factory=list)
    statistics: Dict[str, Statistics] = Field(default_factory=dict)


class Evidence(BaseModel):
    """Verification evidence"""
    source: str
    value: Any
    timestamp: int


class VerifiedClaim(BaseModel):
    """Verified claim"""
    id: str
    statement: str
    metric: str
    value: Any
    verified: bool
    confidence: float
    sources: List[str]
    evidence: List[Evidence]


class DataConflict(BaseModel):
    """Data conflict between sources"""
    claim_id: str
    sources: List[Dict[str, Any]]
    resolution: Optional[str] = None


class AuditEntry(BaseModel):
    """Audit trail entry"""
    timestamp: datetime
    action: str
    claim_id: str
    result: str
    details: Dict[str, Any]


class FactCheckResponse(BaseModel):
    """Fact check results"""
    verified_claims: List[VerifiedClaim] = Field(default_factory=list)
    conflicts: List[DataConflict] = Field(default_factory=list)
    audit_trail: List[AuditEntry] = Field(default_factory=list)
    overall_confidence: float


class ReportDocument(BaseModel):
    """Report document"""
    report_id: str
    user_id: str
    query_id: str
    query: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    report: Report
    analysis_results: AnalysisResponse
    fact_check_results: Optional[FactCheckResponse] = None
    visualization_urls: List[str] = Field(default_factory=list)
    expires_at: datetime

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection name
REPORT_COLLECTION = "reports"

# Index specifications
REPORT_INDEXES = [
    {"keys": [("report_id", 1)], "unique": True, "name": "idx_reportId"},
    {"keys": [("user_id", 1)], "name": "idx_userId"},
    {"keys": [("query_id", 1)], "name": "idx_queryId"},
    {"keys": [("user_id", 1), ("created_at", -1)], "name": "idx_userId_createdAt"},
    {
        "keys": [("expires_at", 1)],
        "expireAfterSeconds": 0,
        "name": "idx_ttl"
    },
]
