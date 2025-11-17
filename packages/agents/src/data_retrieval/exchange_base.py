"""Base class for exchange API adapters"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
import httpx

from .exchange_types import MarketData, OrderBookData, TradeData


logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_second: float):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.requests_per_second,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ExchangeAdapter(ABC):
    """
    Abstract base class for exchange API adapters.
    
    Implements rate limiting and request queuing.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        requests_per_second: float = 10.0,
        timeout: float = 30.0
    ):
        """
        Initialize exchange adapter.
        
        Args:
            api_key: API key for authentication
            api_secret: API secret for authentication
            requests_per_second: Rate limit
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limiter = RateLimiter(requests_per_second)
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(timeout=timeout)
        self.ws_client = None
        
        logger.info(f"Initialized {self.exchange_name} adapter")
    
    @property
    @abstractmethod
    def exchange_name(self) -> str:
        """Exchange name identifier"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for REST API"""
        pass
    
    @property
    @abstractmethod
    def ws_url(self) -> str:
        """WebSocket URL for real-time data"""
        pass
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> dict:
        """
        Make rate-limited HTTP request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            headers: Request headers
            
        Returns:
            Response JSON
        """
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"{self.exchange_name} request failed: {e}")
            raise
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get current market data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "ZEC/USD")
            
        Returns:
            Market data
        """
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBookData:
        """
        Get order book snapshot.
        
        Args:
            symbol: Trading pair symbol
            depth: Number of price levels
            
        Returns:
            Order book data
        """
        pass
    
    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[TradeData]:
        """
        Get recent trades.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades to fetch
            
        Returns:
            List of recent trades
        """
        pass
    
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to exchange format.
        
        Args:
            symbol: Standard symbol (e.g., "ZEC/USD")
            
        Returns:
            Exchange-specific symbol format
        """
        pass
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self.client.aclose()
        if self.ws_client:
            await self.ws_client.close()
        logger.info(f"Closed {self.exchange_name} adapter")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
