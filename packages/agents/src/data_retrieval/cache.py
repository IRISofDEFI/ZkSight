"""Redis caching layer for data retrieval"""
import json
import logging
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as redis

from ..config import RedisConfig


logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """
    Generate consistent cache keys for different data types.
    
    Uses a hierarchical key structure: {namespace}:{type}:{identifier}
    """
    
    @staticmethod
    def _hash_params(params: Dict[str, Any]) -> str:
        """
        Create hash of parameters for cache key.
        
        Args:
            params: Parameters dictionary
            
        Returns:
            Hash string
        """
        # Sort keys for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:8]
    
    @staticmethod
    def block_data(height: int) -> str:
        """Generate key for block data"""
        return f"zcash:block:{height}"
    
    @staticmethod
    def transaction_counts(start: int, end: int) -> str:
        """Generate key for transaction counts"""
        return f"zcash:tx_counts:{start}:{end}"
    
    @staticmethod
    def shielded_pool() -> str:
        """Generate key for shielded pool metrics"""
        return f"zcash:shielded_pool:current"
    
    @staticmethod
    def market_data(exchange: str, symbol: str) -> str:
        """Generate key for market data"""
        symbol_clean = symbol.replace("/", "_")
        return f"market:{exchange}:{symbol_clean}"
    
    @staticmethod
    def order_book(exchange: str, symbol: str, depth: int) -> str:
        """Generate key for order book"""
        symbol_clean = symbol.replace("/", "_")
        return f"orderbook:{exchange}:{symbol_clean}:{depth}"
    
    @staticmethod
    def social_mentions(platform: str, params: Dict[str, Any]) -> str:
        """Generate key for social mentions"""
        param_hash = CacheKeyGenerator._hash_params(params)
        return f"social:{platform}:mentions:{param_hash}"
    
    @staticmethod
    def developer_activity(repo: str, days: int) -> str:
        """Generate key for developer activity"""
        repo_clean = repo.replace("/", "_")
        return f"github:{repo_clean}:activity:{days}d"


class DataCache:
    """
    Redis-based caching layer with TTL support.
    
    Implements different TTL strategies for different data types:
    - On-chain data: 5 minutes
    - Market data: 1 minute
    - Social data: 15 minutes
    """
    
    # Default TTL values in seconds
    TTL_ONCHAIN = 300  # 5 minutes
    TTL_MARKET = 60  # 1 minute
    TTL_SOCIAL = 900  # 15 minutes
    TTL_DEVELOPER = 3600  # 1 hour
    
    def __init__(self, config: RedisConfig):
        """
        Initialize cache with Redis configuration.
        
        Args:
            config: Redis configuration
        """
        self.config = config
        self.redis: Optional[redis.Redis] = None
        self.key_gen = CacheKeyGenerator()
        
        logger.info("Initialized DataCache")
    
    async def connect(self):
        """Establish Redis connection"""
        if self.redis:
            return
        
        self.redis = await redis.Redis(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            db=self.config.db,
            decode_responses=True
        )
        
        # Test connection
        await self.redis.ping()
        logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.redis:
            await self.connect()
        
        try:
            serialized = json.dumps(value, default=str)
            
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        if not self.redis:
            await self.connect()
        
        try:
            result = await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "zcash:block:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis:
            await self.connect()
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidate error for {pattern}: {e}")
            return 0
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Get from cache or fetch and cache if not found.
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch data
            ttl: Time to live in seconds
            *args: Arguments for fetch function
            **kwargs: Keyword arguments for fetch function
            
        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Fetch data
        try:
            data = await fetch_func(*args, **kwargs)
            
            # Cache the result
            if data is not None:
                await self.set(key, data, ttl)
            
            return data
            
        except Exception as e:
            logger.error(f"Fetch error for {key}: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class CachedDataRetrieval:
    """
    Wrapper for data retrieval operations with automatic caching.
    
    Provides convenience methods that handle caching transparently.
    """
    
    def __init__(self, cache: DataCache):
        """
        Initialize cached data retrieval.
        
        Args:
            cache: DataCache instance
        """
        self.cache = cache
    
    async def get_block_data(self, zcash_client, height: int):
        """
        Get block data with caching.
        
        Args:
            zcash_client: ZcashRPCClient instance
            height: Block height
            
        Returns:
            Block data
        """
        key = self.cache.key_gen.block_data(height)
        
        async def fetch():
            data = await zcash_client.get_block_data(height)
            return data.model_dump()
        
        return await self.cache.get_or_fetch(
            key,
            fetch,
            ttl=DataCache.TTL_ONCHAIN
        )
    
    async def get_market_data(self, exchange_adapter, symbol: str):
        """
        Get market data with caching.
        
        Args:
            exchange_adapter: Exchange adapter instance
            symbol: Trading pair symbol
            
        Returns:
            Market data
        """
        key = self.cache.key_gen.market_data(
            exchange_adapter.exchange_name,
            symbol
        )
        
        async def fetch():
            data = await exchange_adapter.get_market_data(symbol)
            return data.model_dump()
        
        return await self.cache.get_or_fetch(
            key,
            fetch,
            ttl=DataCache.TTL_MARKET
        )
    
    async def get_social_mentions(
        self,
        social_client,
        platform: str,
        **params
    ):
        """
        Get social mentions with caching.
        
        Args:
            social_client: Social client instance
            platform: Platform name
            **params: Query parameters
            
        Returns:
            List of mentions
        """
        key = self.cache.key_gen.social_mentions(platform, params)
        
        async def fetch():
            # Call appropriate method based on platform
            if platform == "twitter":
                mentions = await social_client.search_mentions(**params)
            elif platform == "reddit":
                mentions = await social_client.search_subreddit(**params)
            else:
                return []
            
            return [m.model_dump() for m in mentions]
        
        return await self.cache.get_or_fetch(
            key,
            fetch,
            ttl=DataCache.TTL_SOCIAL
        )
