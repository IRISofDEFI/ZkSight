"""Query history models for MongoDB"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """Time range specification"""
    start: str
    end: str


class QueryIntent(BaseModel):
    """Query intent classification"""
    type: str
    time_range: TimeRange
    metrics: List[str]
    confidence: float


class ExtractedEntity(BaseModel):
    """Extracted entity from query"""
    type: str
    value: str
    confidence: float
    position: Dict[str, int]


class ConversationContext(BaseModel):
    """Conversation context"""
    previous_queries: List[str] = Field(default_factory=list)
    entities: Dict[str, Any] = Field(default_factory=dict)
    time_range: Optional[TimeRange] = None
    metrics: Optional[List[str]] = None


class QueryResults(BaseModel):
    """Query execution results"""
    report_id: str
    execution_time: float
    data_sources_used: List[str]
    records_processed: int


class QueryError(BaseModel):
    """Query error information"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class QueryHistory(BaseModel):
    """Query history document"""
    query_id: str
    user_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: str
    intent: QueryIntent
    entities: List[ExtractedEntity] = Field(default_factory=list)
    context: Optional[ConversationContext] = None
    status: str = "pending"
    results: Optional[QueryResults] = None
    error: Optional[QueryError] = None
    clarification_needed: bool = False
    clarification_questions: Optional[List[str]] = None
    clarification_response: Optional[str] = None

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection name
QUERY_HISTORY_COLLECTION = "query_history"

# Index specifications
QUERY_HISTORY_INDEXES = [
    {"keys": [("query_id", 1)], "unique": True, "name": "idx_queryId"},
    {"keys": [("user_id", 1)], "name": "idx_userId"},
    {"keys": [("session_id", 1)], "name": "idx_sessionId"},
    {"keys": [("user_id", 1), ("timestamp", -1)], "name": "idx_userId_timestamp"},
    {"keys": [("status", 1)], "name": "idx_status"},
    {"keys": [("intent.type", 1)], "name": "idx_intentType"},
    {"keys": [("timestamp", -1)], "name": "idx_timestamp"},
]
