"""InfluxDB measurement schemas and utilities"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError

from ..config import load_config


class MetricType(str, Enum):
    """Metric types for tagging"""
    NETWORK = "network"
    MARKET = "market"
    SOCIAL = "social"


class DataSource(str, Enum):
    """Data source types"""
    NODE = "node"
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    TWITTER = "twitter"
    REDDIT = "reddit"
    GITHUB = "github"


class NetworkType(str, Enum):
    """Network types"""
    MAINNET = "mainnet"
    TESTNET = "testnet"


# Measurement name for all Zcash metrics
ZCASH_METRICS_MEASUREMENT = "zcash_metrics"

# Retention policy configurations
RETENTION_POLICIES = {
    "hot": {
        "name": "hot_storage",
        "duration": "365d",  # 1 year
        "shard_duration": "1d",
        "replication": 1,
    },
    "cold": {
        "name": "cold_storage",
        "duration": "1095d",  # 3 years
        "shard_duration": "7d",
        "replication": 1,
    },
}

# Continuous query configurations for downsampling
CONTINUOUS_QUERIES = [
    {
        "name": "downsample_hourly",
        "query": f"""
            SELECT mean(value) as value, mean(volume) as volume, sum(count) as count
            INTO {ZCASH_METRICS_MEASUREMENT}_hourly
            FROM {ZCASH_METRICS_MEASUREMENT}
            GROUP BY time(1h), metric_type, source, network
        """,
        "interval": "1h",
    },
    {
        "name": "downsample_daily",
        "query": f"""
            SELECT mean(value) as value, mean(volume) as volume, sum(count) as count
            INTO {ZCASH_METRICS_MEASUREMENT}_daily
            FROM {ZCASH_METRICS_MEASUREMENT}_hourly
            GROUP BY time(1d), metric_type, source, network
        """,
        "interval": "1d",
    },
]


_client: Optional[InfluxDBClient] = None
_write_api = None
_query_api = None


def initialize_influxdb() -> InfluxDBClient:
    """Initialize InfluxDB connection"""
    global _client, _write_api, _query_api
    
    if _client is not None:
        return _client
    
    config = load_config()
    
    try:
        _client = InfluxDBClient(
            url=config.influxdb.url,
            token=config.influxdb.token,
            org=config.influxdb.org,
            timeout=30000,
        )
        
        # Test connection
        health = _client.health()
        if health.status != "pass":
            raise ConnectionError(f"InfluxDB health check failed: {health.message}")
        
        _write_api = _client.write_api(write_options=ASYNCHRONOUS)
        _query_api = _client.query_api()
        
        print("InfluxDB initialized")
        return _client
    except Exception as e:
        print(f"Failed to initialize InfluxDB: {e}")
        raise


def get_client() -> InfluxDBClient:
    """Get InfluxDB client instance"""
    if _client is None:
        raise RuntimeError("InfluxDB not initialized. Call initialize_influxdb() first.")
    return _client


def get_write_api():
    """Get write API instance"""
    if _write_api is None:
        raise RuntimeError("InfluxDB not initialized. Call initialize_influxdb() first.")
    return _write_api


def get_query_api():
    """Get query API instance"""
    if _query_api is None:
        raise RuntimeError("InfluxDB not initialized. Call initialize_influxdb() first.")
    return _query_api


def create_metric_point(
    metric_name: str,
    value: float,
    metric_type: MetricType,
    source: DataSource,
    network: NetworkType = NetworkType.MAINNET,
    additional_fields: Optional[Dict[str, Any]] = None,
    additional_tags: Optional[Dict[str, str]] = None,
    timestamp: Optional[datetime] = None,
) -> Point:
    """
    Create a data point for zcash_metrics measurement
    
    Args:
        metric_name: Name of the metric
        value: Primary metric value
        metric_type: Type of metric (network, market, social)
        source: Data source
        network: Network type (mainnet, testnet)
        additional_fields: Optional additional numeric fields
        additional_tags: Optional additional tags
        timestamp: Optional timestamp (defaults to now)
    
    Returns:
        Point object ready to be written
    """
    point = (
        Point(ZCASH_METRICS_MEASUREMENT)
        .tag("metric_type", metric_type.value)
        .tag("source", source.value)
        .tag("network", network.value)
        .tag("metric_name", metric_name)
        .field("value", float(value))
    )
    
    # Add optional fields
    if additional_fields:
        for key, val in additional_fields.items():
            if isinstance(val, (int, float)):
                point.field(key, val)
    
    # Add optional tags
    if additional_tags:
        for key, val in additional_tags.items():
            point.tag(key, str(val))
    
    # Set timestamp if provided
    if timestamp:
        point.time(timestamp, WritePrecision.NS)
    
    return point


def write_metric(
    metric_name: str,
    value: float,
    metric_type: MetricType,
    source: DataSource,
    network: NetworkType = NetworkType.MAINNET,
    additional_fields: Optional[Dict[str, Any]] = None,
    additional_tags: Optional[Dict[str, str]] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """Write a single metric point"""
    config = load_config()
    write_api = get_write_api()
    
    point = create_metric_point(
        metric_name,
        value,
        metric_type,
        source,
        network,
        additional_fields,
        additional_tags,
        timestamp,
    )
    
    write_api.write(bucket=config.influxdb.bucket, record=point)


def write_metrics_batch(points: List[Point]) -> None:
    """Write multiple metric points in batch"""
    config = load_config()
    write_api = get_write_api()
    write_api.write(bucket=config.influxdb.bucket, record=points)


def close_influxdb() -> None:
    """Close InfluxDB connection"""
    global _client, _write_api, _query_api
    
    if _client is not None:
        _client.close()
        _client = None
        _write_api = None
        _query_api = None
        print("InfluxDB connection closed")


async def setup_influxdb_schema() -> None:
    """
    Setup retention policies and continuous queries
    Note: This requires admin access and should be run during initial setup
    """
    client = get_client()
    config = load_config()
    
    try:
        buckets_api = client.buckets_api()
        org_api = client.organizations_api()
        
        # Get organization
        orgs = org_api.find_organizations(org=config.influxdb.org)
        if not orgs:
            raise ValueError(f"Organization {config.influxdb.org} not found")
        org_id = orgs[0].id
        
        # Check if bucket exists
        buckets = buckets_api.find_buckets(org_id=org_id).buckets
        bucket_names = [b.name for b in buckets] if buckets else []
        
        if config.influxdb.bucket not in bucket_names:
            # Create bucket with hot storage retention
            buckets_api.create_bucket(
                bucket_name=config.influxdb.bucket,
                org_id=org_id,
                retention_rules=[
                    {"type": "expire", "everySeconds": 365 * 24 * 60 * 60}  # 1 year
                ],
            )
            print(f"Created bucket: {config.influxdb.bucket}")
        
        # Create additional buckets for downsampled data
        downsampled_buckets = [
            {"name": f"{config.influxdb.bucket}_hourly", "retention": 365 * 24 * 60 * 60},
            {"name": f"{config.influxdb.bucket}_daily", "retention": 3 * 365 * 24 * 60 * 60},
        ]
        
        for bucket_config in downsampled_buckets:
            if bucket_config["name"] not in bucket_names:
                buckets_api.create_bucket(
                    bucket_name=bucket_config["name"],
                    org_id=org_id,
                    retention_rules=[
                        {"type": "expire", "everySeconds": bucket_config["retention"]}
                    ],
                )
                print(f"Created bucket: {bucket_config['name']}")
        
        print("InfluxDB schema setup completed")
    except InfluxDBError as e:
        print(f"InfluxDB setup error: {e}")
        raise


async def check_influxdb_health() -> bool:
    """Health check for InfluxDB connection"""
    try:
        if _client is None:
            return False
        health = _client.health()
        return health.status == "pass"
    except Exception as e:
        print(f"InfluxDB health check failed: {e}")
        return False
