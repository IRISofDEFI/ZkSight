"""Type definitions for Data Retrieval Agent"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BlockData(BaseModel):
    """Zcash block data"""
    height: int = Field(description="Block height")
    hash: str = Field(description="Block hash")
    timestamp: datetime = Field(description="Block timestamp")
    difficulty: float = Field(description="Block difficulty")
    size: int = Field(description="Block size in bytes")
    tx_count: int = Field(description="Number of transactions")
    shielded_tx_count: int = Field(description="Number of shielded transactions")


class TransactionCounts(BaseModel):
    """Transaction count metrics"""
    total: int = Field(description="Total transaction count")
    shielded: int = Field(description="Shielded transaction count")
    transparent: int = Field(description="Transparent transaction count")
    shielded_percentage: float = Field(description="Percentage of shielded transactions")


class ShieldedPoolMetrics(BaseModel):
    """Shielded pool metrics"""
    sprout_pool_value: float = Field(description="Sprout pool value in ZEC")
    sapling_pool_value: float = Field(description="Sapling pool value in ZEC")
    orchard_pool_value: float = Field(description="Orchard pool value in ZEC")
    total_shielded_value: float = Field(description="Total shielded value in ZEC")


class DataPoint(BaseModel):
    """Generic data point"""
    timestamp: datetime = Field(description="Data point timestamp")
    metric: str = Field(description="Metric name")
    value: float | str = Field(description="Metric value")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional tags")


class DataSourceError(BaseModel):
    """Data source error information"""
    source: str = Field(description="Data source name")
    error: str = Field(description="Error message")
    retryable: bool = Field(description="Whether the error is retryable")


class DataRetrievalRequest(BaseModel):
    """Request for data retrieval"""
    request_id: str = Field(description="Unique request identifier")
    sources: List[str] = Field(description="Data sources to query")
    time_range: Optional[Dict[str, Any]] = Field(default=None, description="Time range filter")
    metrics: List[str] = Field(description="Metrics to retrieve")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")


class DataRetrievalResponse(BaseModel):
    """Response from data retrieval"""
    request_id: str = Field(description="Request identifier")
    data: Dict[str, List[DataPoint]] = Field(description="Retrieved data by source")
    metadata: List[Dict[str, Any]] = Field(description="Metadata for each source")
    errors: List[DataSourceError] = Field(default_factory=list, description="Errors encountered")
    cached: bool = Field(default=False, description="Whether data was served from cache")
