"""
Example demonstrating structured logging usage in Chimera agents.

This example shows how to:
1. Set up structured logging
2. Use correlation IDs
3. Add context to logs
4. Log different severity levels
5. Log errors with stack traces
"""
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.logging import (
    setup_logging,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id,
    LoggerAdapter,
    log_with_context,
    log_agent_start,
    log_agent_stop,
    log_message_received,
    log_message_sent,
    log_error,
)


def example_basic_logging():
    """Example 1: Basic structured logging"""
    print("\n=== Example 1: Basic Structured Logging ===\n")
    
    # Set up logging
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    # Log at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("\n✅ Basic logging complete\n")


def example_correlation_id():
    """Example 2: Using correlation IDs"""
    print("\n=== Example 2: Correlation ID Tracking ===\n")
    
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    # Set correlation ID for request tracking
    correlation_id = "req-12345-abcde"
    set_correlation_id(correlation_id)
    
    logger.info("Processing request")
    logger.info("Fetching data from database")
    logger.info("Request completed")
    
    # Get current correlation ID
    current_id = get_correlation_id()
    print(f"Current correlation ID: {current_id}")
    
    # Clear correlation ID
    clear_correlation_id()
    logger.info("This log has no correlation ID")
    
    print("\n✅ Correlation ID example complete\n")


def example_context_logging():
    """Example 3: Adding context to logs"""
    print("\n=== Example 3: Context Logging ===\n")
    
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    # Log with additional context
    log_with_context(
        logger,
        'info',
        'User query received',
        user_id='user-123',
        query_id='query-456',
        query_text='What is the current ZEC price?',
        event='query_received'
    )
    
    # Simulate processing
    start_time = time.time()
    time.sleep(0.1)  # Simulate work
    duration = (time.time() - start_time) * 1000
    
    log_with_context(
        logger,
        'info',
        'Query processed successfully',
        user_id='user-123',
        query_id='query-456',
        duration_ms=duration,
        event='query_completed'
    )
    
    print("\n✅ Context logging example complete\n")


def example_logger_adapter():
    """Example 4: Using LoggerAdapter for persistent context"""
    print("\n=== Example 4: Logger Adapter ===\n")
    
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    base_logger = get_logger(__name__)
    
    # Create adapter with persistent context
    logger = LoggerAdapter(base_logger, {
        'agent': 'query-agent',
        'version': '1.0.0'
    })
    
    # All logs will include agent and version
    logger.info("Agent initialized")
    logger.info("Processing query", extra_fields={'query_id': 'q-123'})
    logger.info("Query completed", extra_fields={'duration_ms': 150})
    
    print("\n✅ Logger adapter example complete\n")


def example_agent_lifecycle():
    """Example 5: Agent lifecycle logging"""
    print("\n=== Example 5: Agent Lifecycle Logging ===\n")
    
    setup_logging(service_name="query-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    # Log agent start
    config = {
        'model': 'gpt-4',
        'max_tokens': 1000,
        'temperature': 0.7
    }
    log_agent_start(logger, 'query-agent', config)
    
    # Simulate agent work
    correlation_id = "msg-789-xyz"
    log_message_received(logger, 'query-agent', 'QueryRequest', correlation_id)
    
    time.sleep(0.1)  # Simulate processing
    
    log_message_sent(logger, 'query-agent', 'QueryResponse', correlation_id)
    
    # Log agent stop
    log_agent_stop(logger, 'query-agent')
    
    print("\n✅ Agent lifecycle example complete\n")


def example_error_logging():
    """Example 6: Error logging with stack traces"""
    print("\n=== Example 6: Error Logging ===\n")
    
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        # Log error with context
        log_error(logger, e, context={
            'operation': 'division',
            'numerator': 10,
            'denominator': 0,
            'user_id': 'user-123'
        })
    
    try:
        # Another error example
        data = {'key': 'value'}
        value = data['missing_key']
    except KeyError as e:
        # Log with exception info
        logger.error(
            "Failed to access key",
            exc_info=True,
            extra={
                'extra_fields': {
                    'key': 'missing_key',
                    'available_keys': list(data.keys()),
                    'event': 'key_error'
                }
            }
        )
    
    print("\n✅ Error logging example complete\n")


def example_multi_service_tracing():
    """Example 7: Multi-service request tracing"""
    print("\n=== Example 7: Multi-Service Tracing ===\n")
    
    # Simulate multiple services processing the same request
    correlation_id = "trace-abc-123"
    
    # Service 1: Query Agent
    setup_logging(service_name="query-agent", log_level="INFO", json_format=True)
    logger1 = get_logger("query-agent")
    set_correlation_id(correlation_id)
    logger1.info("Received user query")
    logger1.info("Parsed query intent")
    
    # Service 2: Data Retrieval Agent
    setup_logging(service_name="data-retrieval-agent", log_level="INFO", json_format=True)
    logger2 = get_logger("data-retrieval-agent")
    set_correlation_id(correlation_id)
    logger2.info("Fetching blockchain data")
    logger2.info("Data retrieved successfully")
    
    # Service 3: Analysis Agent
    setup_logging(service_name="analysis-agent", log_level="INFO", json_format=True)
    logger3 = get_logger("analysis-agent")
    set_correlation_id(correlation_id)
    logger3.info("Analyzing data")
    logger3.info("Analysis complete")
    
    print(f"\n💡 All logs share correlation_id: {correlation_id}")
    print("   Query in Grafana: {correlation_id=\"trace-abc-123\"}")
    print("\n✅ Multi-service tracing example complete\n")


def example_performance_logging():
    """Example 8: Performance logging"""
    print("\n=== Example 8: Performance Logging ===\n")
    
    setup_logging(service_name="example-agent", log_level="INFO", json_format=True)
    logger = get_logger(__name__)
    
    # Log operation with timing
    operation = "database_query"
    start_time = time.time()
    
    # Simulate work
    time.sleep(0.15)
    
    duration_ms = (time.time() - start_time) * 1000
    
    log_with_context(
        logger,
        'info',
        f'{operation} completed',
        operation=operation,
        duration_ms=duration_ms,
        success=True,
        rows_affected=42,
        event='performance_metric'
    )
    
    # Log slow operation warning
    if duration_ms > 100:
        log_with_context(
            logger,
            'warning',
            f'{operation} was slow',
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=100,
            event='slow_operation'
        )
    
    print("\n✅ Performance logging example complete\n")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Chimera Structured Logging Examples")
    print("="*60)
    
    examples = [
        example_basic_logging,
        example_correlation_id,
        example_context_logging,
        example_logger_adapter,
        example_agent_lifecycle,
        example_error_logging,
        example_multi_service_tracing,
        example_performance_logging,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Example failed: {e}\n")
    
    print("="*60)
    print("All examples complete!")
    print("="*60)
    print("\n📚 Next Steps:")
    print("   1. Start the log aggregation stack: docker-compose up -d")
    print("   2. Access Grafana: http://localhost:3000 (admin/admin)")
    print("   3. View logs in the 'Chimera Application Logs' dashboard")
    print("   4. Try querying by correlation_id, service, or level")
    print("\n")


if __name__ == "__main__":
    main()
