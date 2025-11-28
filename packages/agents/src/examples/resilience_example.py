"""
Example usage of resilience patterns (retry and circuit breaker).

This module demonstrates how to use retry logic and circuit breakers
to handle failures in external service calls.
"""
import asyncio
import random
from typing import Dict, Any

from ..resilience import (
    retry,
    RetryStrategy,
    CircuitBreaker,
    circuit_breaker,
    withFallback,
    register_circuit_breaker,
)
from ..errors import DataSourceError, ErrorCode
from ..logging import get_logger

logger = get_logger(__name__)


# Example 1: Using retry decorator with exponential backoff
@retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL, base_delay=1.0)
def fetch_data_from_api(url: str) -> Dict[str, Any]:
    """
    Fetch data from an external API with automatic retry.
    
    This function will automatically retry up to 3 times with exponential backoff
    if the API call fails.
    """
    logger.info(f"Fetching data from {url}")
    
    # Simulate API call that might fail
    if random.random() < 0.3:  # 30% chance of failure
        raise DataSourceError(
            "API temporarily unavailable",
            source=url,
            code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
            retryable=True,
        )
    
    return {"status": "success", "data": [1, 2, 3]}


# Example 2: Using circuit breaker decorator
@circuit_breaker(failure_threshold=5, recovery_timeout=60.0, name="exchange_api")
def fetch_exchange_data(exchange: str) -> Dict[str, Any]:
    """
    Fetch data from exchange API with circuit breaker protection.
    
    If the exchange API fails 5 times, the circuit breaker will open
    and reject requests for 60 seconds to allow the service to recover.
    """
    logger.info(f"Fetching data from {exchange}")
    
    # Simulate API call
    if random.random() < 0.2:  # 20% chance of failure
        raise DataSourceError(
            f"Exchange {exchange} API error",
            source=exchange,
            code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
            retryable=True,
        )
    
    return {"exchange": exchange, "price": 100.0}


# Example 3: Combining retry and circuit breaker
class DataRetriever:
    """Example class using both retry and circuit breaker patterns"""
    
    def __init__(self):
        # Create circuit breaker for external service
        self.breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
            name="data_service",
        )
        register_circuit_breaker("data_service", self.breaker)
    
    @retry(max_attempts=3, base_delay=0.5)
    def fetch_with_retry(self, source: str) -> Dict[str, Any]:
        """Fetch data with retry logic"""
        return self.breaker.call(self._fetch_data, source)
    
    def _fetch_data(self, source: str) -> Dict[str, Any]:
        """Internal method to fetch data"""
        logger.info(f"Fetching from {source}")
        
        # Simulate API call
        if random.random() < 0.25:  # 25% chance of failure
            raise DataSourceError(
                f"Failed to fetch from {source}",
                source=source,
                code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
                retryable=True,
            )
        
        return {"source": source, "data": "example"}


# Example 4: Graceful degradation with fallback
def fetch_primary_data() -> Dict[str, Any]:
    """Fetch data from primary source"""
    logger.info("Fetching from primary source")
    
    # Simulate failure
    if random.random() < 0.5:
        raise DataSourceError(
            "Primary source unavailable",
            source="primary",
            code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
            retryable=True,
        )
    
    return {"source": "primary", "data": [1, 2, 3]}


def fetch_fallback_data() -> Dict[str, Any]:
    """Fetch data from fallback source"""
    logger.info("Using fallback source")
    return {"source": "fallback", "data": [4, 5, 6]}


def fetch_with_fallback() -> Dict[str, Any]:
    """Fetch data with automatic fallback"""
    return withFallback(
        fetch_primary_data,
        fetch_fallback_data,
        fallback_condition=lambda e: isinstance(e, DataSourceError),
    )


# Example 5: Async retry
@retry(max_attempts=3, base_delay=0.5)
async def fetch_async_data(url: str) -> Dict[str, Any]:
    """Async function with retry logic"""
    logger.info(f"Async fetching from {url}")
    
    # Simulate async API call
    await asyncio.sleep(0.1)
    
    if random.random() < 0.3:
        raise DataSourceError(
            "Async API error",
            source=url,
            code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
            retryable=True,
        )
    
    return {"url": url, "data": "async result"}


def main():
    """Run examples"""
    print("=== Resilience Patterns Examples ===\n")
    
    # Example 1: Retry
    print("1. Retry with exponential backoff:")
    try:
        result = fetch_data_from_api("https://api.example.com/data")
        print(f"   Success: {result}\n")
    except Exception as e:
        print(f"   Failed: {e}\n")
    
    # Example 2: Circuit breaker
    print("2. Circuit breaker:")
    try:
        result = fetch_exchange_data("binance")
        print(f"   Success: {result}\n")
    except Exception as e:
        print(f"   Failed: {e}\n")
    
    # Example 3: Combined retry and circuit breaker
    print("3. Combined retry and circuit breaker:")
    retriever = DataRetriever()
    try:
        result = retriever.fetch_with_retry("external_api")
        print(f"   Success: {result}\n")
    except Exception as e:
        print(f"   Failed: {e}\n")
    
    # Example 4: Graceful degradation
    print("4. Graceful degradation with fallback:")
    try:
        result = fetch_with_fallback()
        print(f"   Success: {result}\n")
    except Exception as e:
        print(f"   Failed: {e}\n")
    
    # Example 5: Async retry
    print("5. Async retry:")
    try:
        result = asyncio.run(fetch_async_data("https://api.example.com/async"))
        print(f"   Success: {result}\n")
    except Exception as e:
        print(f"   Failed: {e}\n")


if __name__ == "__main__":
    main()
