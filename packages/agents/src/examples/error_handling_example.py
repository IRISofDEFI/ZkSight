"""
Example usage of error handling, logging, tracing, and resilience utilities.

This module demonstrates how to use the various error handling and resilience
patterns in Chimera agents.
"""
import asyncio
from typing import Dict, Any

# Import error handling
from ..errors import (
    ChimeraError,
    ErrorCode,
    DataSourceError,
    QueryError,
    create_error_response,
)

# Import logging
from ..logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    log_with_context,
)

# Import tracing
from ..tracing import (
    setup_tracing,
    trace_function,
    trace_agent_operation,
    traced_span,
    trace_external_call,
)

# Import resilience
from ..resilience import (
    retry,
    circuit_breaker,
    CircuitBreaker,
    RetryStrategy,
)


# Example 1: Basic error handling
def example_error_handling():
    """Demonstrate error handling"""
    try:
        # Raise a custom error
        raise DataSourceError(
            message="Failed to connect to Zcash node",
            source="zcash-node",
            code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
            retryable=True,
        )
    except ChimeraError as e:
        # Create standardized error response
        error_response = create_error_response(
            error=e,
            request_id="req-123",
        )
        print(f"Error response: {error_response}")


# Example 2: Structured logging
def example_logging():
    """Demonstrate structured logging"""
    # Setup logging
    setup_logging(service_name="example-agent", log_level="INFO")
    logger = get_logger(__name__)
    
    # Set correlation ID
    set_correlation_id("corr-456")
    
    # Log with context
    log_with_context(
        logger,
        "info",
        "Processing query",
        query_id="q-789",
        user_id="u-123",
        event="query_start",
    )
    
    # Regular logging
    logger.info("Query completed successfully")


# Example 3: Distributed tracing
@trace_agent_operation("process_data")
def example_tracing():
    """Demonstrate distributed tracing"""
    # Setup tracing
    setup_tracing(
        service_name="example-agent",
        jaeger_endpoint="http://localhost:4317",
    )
    
    # Function is automatically traced
    with traced_span("fetch_data", attributes={"source": "api"}):
        # Simulate data fetching
        pass
    
    with trace_external_call("zcash-node", "getblockcount"):
        # Simulate external call
        pass


# Example 4: Retry with exponential backoff
@retry(
    max_attempts=3,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=1.0,
    retryable_exceptions=(DataSourceError,),
)
def example_retry():
    """Demonstrate retry logic"""
    # This function will be retried up to 3 times
    # with exponential backoff if it raises DataSourceError
    import random
    
    if random.random() < 0.7:  # 70% chance of failure
        raise DataSourceError(
            message="Temporary connection issue",
            source="api",
            retryable=True,
        )
    
    return {"status": "success"}


# Example 5: Circuit breaker
@circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=DataSourceError,
    name="zcash-node",
)
def example_circuit_breaker():
    """Demonstrate circuit breaker"""
    # This function is protected by a circuit breaker
    # After 5 failures, the circuit opens and rejects requests
    # for 60 seconds before attempting recovery
    
    # Simulate external call
    import random
    if random.random() < 0.3:  # 30% chance of failure
        raise DataSourceError(
            message="Node unavailable",
            source="zcash-node",
            retryable=True,
        )
    
    return {"block_height": 12345}


# Example 6: Combining patterns
@trace_agent_operation("fetch_with_resilience")
@retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
@circuit_breaker(failure_threshold=5, name="external-api")
async def example_combined():
    """Demonstrate combining multiple patterns"""
    logger = get_logger(__name__)
    
    try:
        # Simulate async operation
        await asyncio.sleep(0.1)
        
        log_with_context(
            logger,
            "info",
            "External API call successful",
            event="api_call_success",
        )
        
        return {"data": "success"}
    
    except Exception as e:
        log_with_context(
            logger,
            "error",
            f"External API call failed: {e}",
            event="api_call_failed",
            error_type=type(e).__name__,
        )
        raise


# Example 7: Manual circuit breaker control
def example_manual_circuit_breaker():
    """Demonstrate manual circuit breaker control"""
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30.0,
        name="manual-breaker",
    )
    
    def risky_operation():
        import random
        if random.random() < 0.5:
            raise Exception("Random failure")
        return "success"
    
    # Use circuit breaker
    try:
        result = breaker.call(risky_operation)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Check circuit state
    print(f"Circuit state: {breaker.state}")
    print(f"Failure count: {breaker.failure_count}")
    
    # Manually reset if needed
    if breaker.state == "open":
        breaker.reset()


if __name__ == "__main__":
    print("=== Error Handling Example ===")
    example_error_handling()
    
    print("\n=== Logging Example ===")
    example_logging()
    
    print("\n=== Retry Example ===")
    try:
        result = example_retry()
        print(f"Retry succeeded: {result}")
    except Exception as e:
        print(f"Retry failed: {e}")
    
    print("\n=== Circuit Breaker Example ===")
    for i in range(10):
        try:
            result = example_circuit_breaker()
            print(f"Call {i+1} succeeded: {result}")
        except Exception as e:
            print(f"Call {i+1} failed: {e}")
    
    print("\n=== Manual Circuit Breaker Example ===")
    example_manual_circuit_breaker()
