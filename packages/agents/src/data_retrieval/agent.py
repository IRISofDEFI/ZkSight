"""Data Retrieval Agent implementation"""
import logging
import asyncio
from typing import Dict, Any, Type, Optional, List
from google.protobuf.message import Message as ProtoMessage

from ..messaging.base_agent import BaseAgent
from ..messaging.connection import ConnectionPool
from ..config import AgentConfig, InfluxDBConfig, RedisConfig
from .zcash_client import ZcashRPCClient, ZcashRPCConfig
from .exchanges import BinanceAdapter, CoinbaseAdapter, KrakenAdapter
from .social import TwitterClient, RedditClient, GitHubClient
from .cache import DataCache, CachedDataRetrieval
from .storage import TimeSeriesStorage
from .types import (
    DataRetrievalRequest,
    DataRetrievalResponse,
    DataPoint,
    DataSourceError,
)


logger = logging.getLogger(__name__)


class DataRetrievalAgent(BaseAgent):
    """
    Data Retrieval Agent for fetching on-chain, market, and social data.
    
    Subscribes to data retrieval request events and publishes response events.
    Implements caching and storage for retrieved data.
    """
    
    def __init__(
        self,
        connection_pool: ConnectionPool,
        config: AgentConfig,
        zcash_config: Optional[ZcashRPCConfig] = None,
        twitter_token: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        github_token: Optional[str] = None,
        binance_key: Optional[str] = None,
        binance_secret: Optional[str] = None,
        coinbase_key: Optional[str] = None,
        coinbase_secret: Optional[str] = None,
        kraken_key: Optional[str] = None,
        kraken_secret: Optional[str] = None,
    ):
        """
        Initialize Data Retrieval Agent.
        
        Args:
            connection_pool: RabbitMQ connection pool
            config: Agent configuration
            zcash_config: Zcash RPC configuration
            twitter_token: Twitter API bearer token
            reddit_client_id: Reddit client ID
            reddit_client_secret: Reddit client secret
            github_token: GitHub access token
            binance_key: Binance API key
            binance_secret: Binance API secret
            coinbase_key: Coinbase API key
            coinbase_secret: Coinbase API secret
            kraken_key: Kraken API key
            kraken_secret: Kraken API secret
        """
        super().__init__(
            connection_pool=connection_pool,
            agent_name="data_retrieval_agent",
            exchange_name="chimera.events",
            routing_keys=["data_retrieval.request"],
            prefetch_count=5,
        )
        
        self.config = config
        
        # Initialize Zcash client
        self.zcash_config = zcash_config or ZcashRPCConfig()
        self.zcash_client: Optional[ZcashRPCClient] = None
        
        # Initialize exchange adapters
        self.exchanges: Dict[str, Any] = {}
        if binance_key:
            self.exchanges["binance"] = BinanceAdapter(
                api_key=binance_key,
                api_secret=binance_secret,
                requests_per_second=10.0
            )
        if coinbase_key:
            self.exchanges["coinbase"] = CoinbaseAdapter(
                api_key=coinbase_key,
                api_secret=coinbase_secret,
                requests_per_second=5.0
            )
        if kraken_key:
            self.exchanges["kraken"] = KrakenAdapter(
                api_key=kraken_key,
                api_secret=kraken_secret,
                requests_per_second=3.0
            )
        
        # Initialize social clients
        self.twitter_client: Optional[TwitterClient] = None
        if twitter_token:
            self.twitter_client = TwitterClient(bearer_token=twitter_token)
        
        self.reddit_client: Optional[RedditClient] = None
        if reddit_client_id and reddit_client_secret:
            self.reddit_client = RedditClient(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret
            )
        
        self.github_client: Optional[GitHubClient] = None
        if github_token:
            self.github_client = GitHubClient(access_token=github_token)
        
        # Initialize cache
        self.cache = DataCache(config.redis)
        self.cached_retrieval = CachedDataRetrieval(self.cache)
        
        # Initialize storage
        self.storage = TimeSeriesStorage(config.influxdb)
        
        logger.info("Initialized Data Retrieval Agent")
    
    async def initialize(self):
        """Initialize async resources"""
        # Connect to cache
        await self.cache.connect()
        
        # Connect to storage
        self.storage.connect()
        
        # Initialize Zcash client
        self.zcash_client = ZcashRPCClient(self.zcash_config)
        
        logger.info("Data Retrieval Agent initialized and ready")
    
    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        """
        Map routing keys to Protocol Buffer message classes.
        
        Returns:
            Dictionary mapping routing keys to message classes
        """
        # Note: In a full implementation, these would be actual protobuf classes
        # For now, we'll use a placeholder approach
        return {
            "data_retrieval.request": dict,  # Placeholder
        }
    
    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Route incoming messages to appropriate handlers.
        
        Args:
            message: Deserialized message
            routing_key: Message routing key
            properties: Message properties
        """
        correlation_id = properties.get("correlation_id")
        
        if routing_key == "data_retrieval.request":
            # Handle data retrieval request
            asyncio.create_task(
                self._handle_data_request(message, correlation_id)
            )
        else:
            logger.warning(f"Unknown routing key: {routing_key}")
    
    async def _handle_data_request(
        self,
        message: Dict[str, Any],
        correlation_id: str
    ):
        """
        Handle data retrieval request.
        
        Args:
            message: Request message
            correlation_id: Request correlation ID
        """
        try:
            # Parse request
            request = DataRetrievalRequest(**message)
            
            logger.info(
                f"Processing data request {request.request_id} "
                f"for sources: {request.sources}"
            )
            
            # Retrieve data from requested sources
            data: Dict[str, List[DataPoint]] = {}
            metadata: List[Dict[str, Any]] = []
            errors: List[DataSourceError] = []
            
            for source in request.sources:
                try:
                    if source == "zcash_node":
                        source_data = await self._fetch_zcash_data(request)
                        data[source] = source_data
                        metadata.append({
                            "source": source,
                            "timestamp": asyncio.get_event_loop().time(),
                            "cached": False
                        })
                    
                    elif source in self.exchanges:
                        source_data = await self._fetch_market_data(
                            source,
                            request
                        )
                        data[source] = source_data
                        metadata.append({
                            "source": source,
                            "timestamp": asyncio.get_event_loop().time(),
                            "cached": False
                        })
                    
                    elif source == "twitter" and self.twitter_client:
                        source_data = await self._fetch_twitter_data(request)
                        data[source] = source_data
                        metadata.append({
                            "source": source,
                            "timestamp": asyncio.get_event_loop().time(),
                            "cached": False
                        })
                    
                    elif source == "reddit" and self.reddit_client:
                        source_data = await self._fetch_reddit_data(request)
                        data[source] = source_data
                        metadata.append({
                            "source": source,
                            "timestamp": asyncio.get_event_loop().time(),
                            "cached": False
                        })
                    
                    elif source == "github" and self.github_client:
                        source_data = await self._fetch_github_data(request)
                        data[source] = source_data
                        metadata.append({
                            "source": source,
                            "timestamp": asyncio.get_event_loop().time(),
                            "cached": False
                        })
                    
                    else:
                        logger.warning(f"Unknown or unavailable source: {source}")
                        errors.append(DataSourceError(
                            source=source,
                            error="Source not available or not configured",
                            retryable=False
                        ))
                
                except Exception as e:
                    logger.error(f"Error fetching from {source}: {e}")
                    errors.append(DataSourceError(
                        source=source,
                        error=str(e),
                        retryable=True
                    ))
            
            # Store data in InfluxDB
            if data:
                await self._store_data(data)
            
            # Create response
            response = DataRetrievalResponse(
                request_id=request.request_id,
                data=data,
                metadata=metadata,
                errors=errors,
                cached=False
            )
            
            # Publish response
            self.publish_response(
                message=response.model_dump(),
                routing_key="data_retrieval.response",
                correlation_id=correlation_id
            )
            
            logger.info(f"Completed data request {request.request_id}")
            
        except Exception as e:
            logger.error(f"Error handling data request: {e}", exc_info=True)
            
            # Publish error response
            error_response = DataRetrievalResponse(
                request_id=message.get("request_id", "unknown"),
                data={},
                metadata=[],
                errors=[DataSourceError(
                    source="data_retrieval_agent",
                    error=str(e),
                    retryable=False
                )],
                cached=False
            )
            
            self.publish_response(
                message=error_response.model_dump(),
                routing_key="data_retrieval.error",
                correlation_id=correlation_id
            )
    
    async def _fetch_zcash_data(
        self,
        request: DataRetrievalRequest
    ) -> List[DataPoint]:
        """Fetch Zcash on-chain data"""
        from datetime import datetime
        
        data_points = []
        
        for metric in request.metrics:
            if metric == "block_data":
                # Get current block height
                height = await self.zcash_client.get_block_count()
                block_data = await self.zcash_client.get_block_data(height)
                
                data_points.append(DataPoint(
                    timestamp=block_data.timestamp,
                    metric="block_height",
                    value=block_data.height,
                    tags={"source": "zcash_node", "metric_type": "network"}
                ))
            
            elif metric == "shielded_pool":
                pool_metrics = await self.zcash_client.get_shielded_pool_metrics()
                
                data_points.append(DataPoint(
                    timestamp=datetime.utcnow(),
                    metric="shielded_pool_total",
                    value=pool_metrics.total_shielded_value,
                    tags={"source": "zcash_node", "metric_type": "network"}
                ))
        
        return data_points
    
    async def _fetch_market_data(
        self,
        exchange: str,
        request: DataRetrievalRequest
    ) -> List[DataPoint]:
        """Fetch market data from exchange"""
        data_points = []
        adapter = self.exchanges[exchange]
        
        for metric in request.metrics:
            if metric.startswith("price_"):
                symbol = metric.replace("price_", "").replace("_", "/").upper()
                market_data = await adapter.get_market_data(symbol)
                
                data_points.append(DataPoint(
                    timestamp=market_data.timestamp,
                    metric=f"price_{symbol}",
                    value=market_data.price,
                    tags={"source": exchange, "metric_type": "market"}
                ))
        
        return data_points
    
    async def _fetch_twitter_data(
        self,
        request: DataRetrievalRequest
    ) -> List[DataPoint]:
        """Fetch Twitter mentions"""
        from datetime import datetime
        
        mentions = await self.twitter_client.search_mentions()
        sentiment = await self.twitter_client.get_sentiment_summary(mentions)
        
        return [DataPoint(
            timestamp=datetime.utcnow(),
            metric="twitter_mentions",
            value=sentiment.mention_count,
            tags={"source": "twitter", "metric_type": "social"}
        )]
    
    async def _fetch_reddit_data(
        self,
        request: DataRetrievalRequest
    ) -> List[DataPoint]:
        """Fetch Reddit posts"""
        from datetime import datetime
        
        posts = await self.reddit_client.get_hot_posts()
        sentiment = await self.reddit_client.get_sentiment_summary(posts)
        
        return [DataPoint(
            timestamp=datetime.utcnow(),
            metric="reddit_posts",
            value=sentiment.mention_count,
            tags={"source": "reddit", "metric_type": "social"}
        )]
    
    async def _fetch_github_data(
        self,
        request: DataRetrievalRequest
    ) -> List[DataPoint]:
        """Fetch GitHub activity"""
        activity = await self.github_client.get_developer_activity()
        
        return [DataPoint(
            timestamp=activity.timestamp,
            metric="github_commits",
            value=activity.commits_count,
            tags={"source": "github", "metric_type": "developer"}
        )]
    
    async def _store_data(self, data: Dict[str, List[DataPoint]]):
        """Store retrieved data in InfluxDB"""
        all_points = []
        for source, points in data.items():
            all_points.extend(points)
        
        if all_points:
            self.storage.write_batch(all_points)
            logger.info(f"Stored {len(all_points)} data points in InfluxDB")
    
    async def cleanup(self):
        """Cleanup async resources"""
        if self.zcash_client:
            await self.zcash_client.close()
        
        for exchange in self.exchanges.values():
            await exchange.close()
        
        if self.twitter_client:
            await self.twitter_client.close()
        
        if self.reddit_client:
            await self.reddit_client.close()
        
        if self.github_client:
            await self.github_client.close()
        
        await self.cache.close()
        self.storage.close()
        
        logger.info("Data Retrieval Agent cleanup complete")
