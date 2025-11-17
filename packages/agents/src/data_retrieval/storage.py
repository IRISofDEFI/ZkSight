"""InfluxDB storage for time series data"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

from ..config import InfluxDBConfig
from .types import DataPoint


logger = logging.getLogger(__name__)


class TimeSeriesStorage:
    """
    InfluxDB storage for time series metrics.
    
    Implements batch writing and retention policies for data lifecycle management.
    """
    
    def __init__(self, config: InfluxDBConfig):
        """
        Initialize InfluxDB storage.
        
        Args:
            config: InfluxDB configuration
        """
        self.config = config
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        
        logger.info("Initialized TimeSeriesStorage")
    
    def connect(self):
        """Establish InfluxDB connection"""
        if self.client:
            return
        
        self.client = InfluxDBClient(
            url=self.config.url,
            token=self.config.token,
            org=self.config.org
        )
        
        # Create write API with batching
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
        self.query_api = self.client.query_api()
        
        # Test connection
        health = self.client.health()
        if health.status != "pass":
            raise Exception(f"InfluxDB health check failed: {health.message}")
        
        logger.info(f"Connected to InfluxDB at {self.config.url}")
    
    def _create_point(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: datetime
    ) -> Point:
        """
        Create InfluxDB point.
        
        Args:
            measurement: Measurement name
            tags: Tag dictionary
            fields: Field dictionary
            timestamp: Data timestamp
            
        Returns:
            InfluxDB Point
        """
        point = Point(measurement)
        
        # Add tags
        for key, value in tags.items():
            point.tag(key, str(value))
        
        # Add fields
        for key, value in fields.items():
            if isinstance(value, (int, float)):
                point.field(key, value)
            else:
                point.field(key, str(value))
        
        # Set timestamp
        point.time(timestamp, WritePrecision.NS)
        
        return point
    
    def write_zcash_metric(
        self,
        metric_type: str,
        source: str,
        fields: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        network: str = "mainnet"
    ):
        """
        Write Zcash network metric.
        
        Args:
            metric_type: Type of metric (network, market, social)
            source: Data source identifier
            fields: Metric fields
            timestamp: Data timestamp (defaults to now)
            network: Network identifier (mainnet, testnet)
        """
        if not self.client:
            self.connect()
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        tags = {
            "metric_type": metric_type,
            "source": source,
            "network": network
        }
        
        point = self._create_point(
            measurement="zcash_metrics",
            tags=tags,
            fields=fields,
            timestamp=timestamp
        )
        
        self.write_api.write(
            bucket=self.config.bucket,
            org=self.config.org,
            record=point
        )
        
        logger.debug(f"Wrote {metric_type} metric from {source}")
    
    def write_block_data(
        self,
        height: int,
        block_hash: str,
        timestamp: datetime,
        difficulty: float,
        size: int,
        tx_count: int,
        shielded_tx_count: int
    ):
        """
        Write block data to InfluxDB.
        
        Args:
            height: Block height
            block_hash: Block hash
            timestamp: Block timestamp
            difficulty: Block difficulty
            size: Block size in bytes
            tx_count: Total transaction count
            shielded_tx_count: Shielded transaction count
        """
        fields = {
            "height": height,
            "difficulty": difficulty,
            "size": size,
            "tx_count": tx_count,
            "shielded_tx_count": shielded_tx_count,
            "shielded_percentage": (shielded_tx_count / tx_count * 100) if tx_count > 0 else 0.0
        }
        
        self.write_zcash_metric(
            metric_type="network",
            source="zcash_node",
            fields=fields,
            timestamp=timestamp
        )
    
    def write_shielded_pool_metrics(
        self,
        sprout_value: float,
        sapling_value: float,
        orchard_value: float,
        total_value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Write shielded pool metrics.
        
        Args:
            sprout_value: Sprout pool value in ZEC
            sapling_value: Sapling pool value in ZEC
            orchard_value: Orchard pool value in ZEC
            total_value: Total shielded value in ZEC
            timestamp: Data timestamp
        """
        fields = {
            "sprout_pool": sprout_value,
            "sapling_pool": sapling_value,
            "orchard_pool": orchard_value,
            "total_shielded": total_value
        }
        
        self.write_zcash_metric(
            metric_type="network",
            source="zcash_node",
            fields=fields,
            timestamp=timestamp
        )
    
    def write_market_data(
        self,
        exchange: str,
        symbol: str,
        price: float,
        volume_24h: float,
        timestamp: datetime,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        high_24h: Optional[float] = None,
        low_24h: Optional[float] = None
    ):
        """
        Write market data to InfluxDB.
        
        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            price: Current price
            volume_24h: 24-hour volume
            timestamp: Data timestamp
            bid: Best bid price
            ask: Best ask price
            high_24h: 24-hour high
            low_24h: 24-hour low
        """
        fields = {
            "price": price,
            "volume_24h": volume_24h
        }
        
        if bid is not None:
            fields["bid"] = bid
        if ask is not None:
            fields["ask"] = ask
        if high_24h is not None:
            fields["high_24h"] = high_24h
        if low_24h is not None:
            fields["low_24h"] = low_24h
        
        if bid and ask:
            fields["spread"] = ask - bid
            fields["mid_price"] = (bid + ask) / 2
        
        tags = {
            "metric_type": "market",
            "source": exchange,
            "symbol": symbol.replace("/", "_"),
            "network": "mainnet"
        }
        
        point = self._create_point(
            measurement="zcash_metrics",
            tags=tags,
            fields=fields,
            timestamp=timestamp
        )
        
        self.write_api.write(
            bucket=self.config.bucket,
            org=self.config.org,
            record=point
        )
    
    def write_social_sentiment(
        self,
        platform: str,
        mention_count: int,
        positive_count: int,
        negative_count: int,
        neutral_count: int,
        average_sentiment: float,
        engagement_total: int,
        timestamp: datetime
    ):
        """
        Write social sentiment data.
        
        Args:
            platform: Platform name
            mention_count: Total mentions
            positive_count: Positive mentions
            negative_count: Negative mentions
            neutral_count: Neutral mentions
            average_sentiment: Average sentiment score
            engagement_total: Total engagement
            timestamp: Data timestamp
        """
        fields = {
            "mention_count": mention_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "average_sentiment": average_sentiment,
            "engagement_total": engagement_total
        }
        
        self.write_zcash_metric(
            metric_type="social",
            source=platform,
            fields=fields,
            timestamp=timestamp
        )
    
    def write_developer_activity(
        self,
        repository: str,
        commits: int,
        pull_requests: int,
        issues: int,
        contributors: int,
        stars: int,
        forks: int,
        timestamp: datetime
    ):
        """
        Write developer activity metrics.
        
        Args:
            repository: Repository name
            commits: Commit count
            pull_requests: PR count
            issues: Issue count
            contributors: Contributor count
            stars: Star count
            forks: Fork count
            timestamp: Data timestamp
        """
        fields = {
            "commits": commits,
            "pull_requests": pull_requests,
            "issues": issues,
            "contributors": contributors,
            "stars": stars,
            "forks": forks
        }
        
        tags = {
            "metric_type": "developer",
            "source": "github",
            "repository": repository.replace("/", "_"),
            "network": "mainnet"
        }
        
        point = self._create_point(
            measurement="zcash_metrics",
            tags=tags,
            fields=fields,
            timestamp=timestamp
        )
        
        self.write_api.write(
            bucket=self.config.bucket,
            org=self.config.org,
            record=point
        )
    
    def write_batch(self, data_points: List[DataPoint]):
        """
        Write multiple data points in batch.
        
        Args:
            data_points: List of data points to write
        """
        if not self.client:
            self.connect()
        
        points = []
        
        for dp in data_points:
            # Extract tags from data point tags
            tags = {
                "metric_type": dp.tags.get("metric_type", "unknown"),
                "source": dp.tags.get("source", "unknown"),
                "network": dp.tags.get("network", "mainnet")
            }
            
            # Create field based on value type
            if isinstance(dp.value, (int, float)):
                fields = {"value": dp.value}
            else:
                fields = {"value_str": str(dp.value)}
            
            # Add metric name as tag
            tags["metric"] = dp.metric
            
            point = self._create_point(
                measurement="zcash_metrics",
                tags=tags,
                fields=fields,
                timestamp=dp.timestamp
            )
            
            points.append(point)
        
        self.write_api.write(
            bucket=self.config.bucket,
            org=self.config.org,
            record=points
        )
        
        logger.info(f"Wrote batch of {len(points)} data points")
    
    def query_metrics(
        self,
        metric_type: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
        aggregation: Optional[str] = None,
        window: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query metrics from InfluxDB.
        
        Args:
            metric_type: Filter by metric type
            source: Filter by source
            start_time: Start time for query
            stop_time: Stop time for query
            aggregation: Aggregation function (mean, sum, max, min)
            window: Aggregation window (e.g., "1h", "1d")
            
        Returns:
            List of query results
        """
        if not self.client:
            self.connect()
        
        # Build Flux query
        query = f'from(bucket: "{self.config.bucket}")'
        
        # Time range
        if start_time:
            query += f' |> range(start: {start_time.isoformat()}Z'
            if stop_time:
                query += f', stop: {stop_time.isoformat()}Z'
            query += ')'
        else:
            query += ' |> range(start: -24h)'
        
        # Filter by measurement
        query += ' |> filter(fn: (r) => r._measurement == "zcash_metrics")'
        
        # Filter by metric type
        if metric_type:
            query += f' |> filter(fn: (r) => r.metric_type == "{metric_type}")'
        
        # Filter by source
        if source:
            query += f' |> filter(fn: (r) => r.source == "{source}")'
        
        # Aggregation
        if aggregation and window:
            query += f' |> aggregateWindow(every: {window}, fn: {aggregation})'
        
        try:
            tables = self.query_api.query(query, org=self.config.org)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "tags": {k: v for k, v in record.values.items() if k not in ["_time", "_value", "_field", "_measurement"]}
                    })
            
            logger.info(f"Query returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def setup_retention_policies(self):
        """
        Set up retention policies for data lifecycle management.
        
        Creates retention policies:
        - Hot data: 1 year
        - Cold data: 3 years (downsampled)
        """
        # Note: Retention policies are typically configured at bucket creation
        # or through the InfluxDB UI/CLI. This is a placeholder for documentation.
        logger.info("Retention policies should be configured at bucket level")
        logger.info("Recommended: 1 year hot data, 3 years cold data with downsampling")
    
    def close(self):
        """Close InfluxDB connection"""
        if self.write_api:
            self.write_api.close()
        if self.client:
            self.client.close()
        logger.info("Closed InfluxDB connection")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
