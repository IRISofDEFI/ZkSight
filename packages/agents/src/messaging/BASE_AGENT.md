# BaseAgent Class

The `BaseAgent` class is the foundation for all agents in the Chimera Analytics system. It combines publisher and subscriber functionality with built-in support for message routing, correlation ID tracking, and dead letter queue handling.

## Overview

`BaseAgent` extends `EventSubscriber` and integrates an `EventPublisher`, providing a complete solution for agent communication. It handles the complexity of message routing, request-response patterns, and correlation tracking, allowing agent implementations to focus on business logic.

## Features

### 1. Unified Publisher/Subscriber Interface

- Single class for both publishing and subscribing
- Automatic setup of exchanges, queues, and bindings
- Built-in dead letter queue (DLQ) configuration

### 2. Message Routing

- Abstract routing key mapping
- Automatic message deserialization
- Type-safe message handling

### 3. Correlation ID Tracking

- Automatic correlation ID generation
- Context storage for request-response patterns
- Correlation cleanup utilities

### 4. Dead Letter Queue Handling

- Automatic DLQ setup for failed messages
- 24-hour TTL for messages in DLQ
- Failed messages automatically routed to DLQ on processing errors

## Usage

### Basic Agent Implementation

```python
from typing import Dict, Any, Type
from google.protobuf.message import Message as ProtoMessage
from messaging import BaseAgent, ConnectionPool
from messaging.generated import messages_pb2

class MyAgent(BaseAgent):
    def __init__(self, connection_pool: ConnectionPool):
        super().__init__(
            connection_pool=connection_pool,
            agent_name="my_agent",
            routing_keys=["my_agent.request", "other_agent.response"],
        )
    
    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        """Map routing keys to message classes"""
        return {
            "my_agent.request": messages_pb2.MyRequest,
            "other_agent.response": messages_pb2.OtherResponse,
        }
    
    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """Route messages to handlers"""
        correlation_id = properties.get("correlation_id")
        
        if routing_key == "my_agent.request":
            self._handle_request(message, correlation_id)
        elif routing_key == "other_agent.response":
            self._handle_response(message, correlation_id)
    
    def _handle_request(self, message, correlation_id):
        # Process request
        print(f"Handling request: {correlation_id}")
        
        # Publish response
        response = messages_pb2.MyResponse()
        self.publish_response(
            message=response,
            routing_key="my_agent.response",
            correlation_id=correlation_id,
        )
```

### Publishing Events

#### Simple Event Publishing

```python
# Publish a one-way event
event = messages_pb2.AlertEvent()
event.alert_type = "price_spike"
event.severity = "high"

self.publish_event(
    message=event,
    routing_key="alert.event",
)
```

#### Request-Response Pattern

```python
# Publish a request expecting a response
request = messages_pb2.DataRequest()
request.source = "blockchain"
request.metric = "transaction_count"

correlation_id = self.publish_request(
    message=request,
    routing_key="data.request",
    reply_routing_key="data.response",
    context={
        "original_query": "What is the transaction count?",
        "user_id": "user123",
    }
)

# Later, when response arrives, retrieve context
def _handle_data_response(self, message, correlation_id):
    context = self.get_correlation_context(correlation_id)
    if context:
        original_query = context["context"]["original_query"]
        # Process response with context
    
    # Clean up correlation
    self.clear_correlation(correlation_id)
```

#### Publishing Responses

```python
# Publish a response to a previous request
def _handle_request(self, message, correlation_id):
    # Process request
    result = self._process_data(message)
    
    # Build response
    response = messages_pb2.DataResponse()
    response.data.extend(result)
    
    # Publish response with same correlation ID
    self.publish_response(
        message=response,
        routing_key="data.response",
        correlation_id=correlation_id,
    )
```

### Correlation ID Management

#### Tracking Request Context

```python
# When publishing a request
correlation_id = self.publish_request(
    message=request,
    routing_key="analysis.request",
    reply_routing_key="analysis.response",
    context={
        "step": "analysis",
        "previous_results": data,
        "user_preferences": preferences,
    }
)

# When handling the response
def _handle_analysis_response(self, message, correlation_id):
    # Retrieve stored context
    context = self.get_correlation_context(correlation_id)
    
    if context:
        step = context["context"]["step"]
        previous_results = context["context"]["previous_results"]
        
        # Use context to process response
        self._continue_workflow(message, previous_results)
    
    # Clean up when done
    self.clear_correlation(correlation_id)
```

#### Cleaning Up Old Correlations

```python
# Periodically clean up old correlation entries
# (e.g., in a background task or before processing messages)
def _periodic_cleanup(self):
    # Remove correlations older than 1 hour
    cleaned = self.cleanup_old_correlations(max_age_seconds=3600)
    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old correlations")
```

### Error Handling

Errors in message handlers are automatically caught and cause messages to be rejected to the DLQ:

```python
def route_message(self, message, routing_key, properties):
    correlation_id = properties.get("correlation_id")
    
    try:
        # Process message
        self._process_message(message)
    except ValueError as e:
        # Log error - message will be sent to DLQ
        logger.error(f"Invalid message: {e}")
        raise  # Re-raise to trigger DLQ routing
    except Exception as e:
        # Unexpected error - also goes to DLQ
        logger.error(f"Processing error: {e}", exc_info=True)
        raise
```

### Running the Agent

```python
from config import load_config
from messaging import ConnectionPool

def main():
    # Load configuration
    config = load_config()
    
    # Create connection pool
    connection_pool = ConnectionPool(config.rabbitmq)
    
    try:
        # Create agent
        agent = MyAgent(connection_pool)
        
        # Start consuming (blocks until stopped)
        agent.start_consuming()
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        connection_pool.close()

if __name__ == "__main__":
    main()
```

## API Reference

### Constructor

```python
def __init__(
    self,
    connection_pool: ConnectionPool,
    agent_name: str,
    exchange_name: str = "chimera.events",
    routing_keys: Optional[List[str]] = None,
    prefetch_count: int = 1,
)
```

**Parameters:**
- `connection_pool`: RabbitMQ connection pool
- `agent_name`: Unique name for this agent (used for queue name)
- `exchange_name`: Exchange to publish/subscribe to (default: "chimera.events")
- `routing_keys`: List of routing key patterns to subscribe to (default: `["{agent_name}.#"]`)
- `prefetch_count`: Number of messages to prefetch (default: 1)

### Abstract Methods

Must be implemented by subclasses:

#### `get_routing_key_map()`

```python
@abstractmethod
def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
    """Map routing keys to Protocol Buffer message classes"""
    pass
```

Returns a dictionary mapping routing key strings to Protocol Buffer message classes.

#### `route_message()`

```python
@abstractmethod
def route_message(
    self,
    message: ProtoMessage,
    routing_key: str,
    properties: Dict[str, Any]
) -> None:
    """Route message to appropriate handler"""
    pass
```

Routes incoming messages to appropriate handler methods based on routing key.

### Publishing Methods

#### `publish_event()`

```python
def publish_event(
    self,
    message: ProtoMessage,
    routing_key: str,
    correlation_id: Optional[str] = None,
) -> str:
```

Publish a one-way event. Returns the correlation ID used.

#### `publish_request()`

```python
def publish_request(
    self,
    message: ProtoMessage,
    routing_key: str,
    reply_routing_key: str,
    context: Optional[Dict[str, Any]] = None,
) -> str:
```

Publish a request expecting a response. Stores context for correlation tracking. Returns the correlation ID.

#### `publish_response()`

```python
def publish_response(
    self,
    message: ProtoMessage,
    routing_key: str,
    correlation_id: str,
) -> None:
```

Publish a response to a previous request using the same correlation ID.

### Correlation Management

#### `get_correlation_context()`

```python
def get_correlation_context(
    self, correlation_id: str
) -> Optional[Dict[str, Any]]:
```

Retrieve stored context for a correlation ID. Returns `None` if not found.

#### `clear_correlation()`

```python
def clear_correlation(self, correlation_id: str) -> None:
```

Remove stored context for a correlation ID.

#### `cleanup_old_correlations()`

```python
def cleanup_old_correlations(self, max_age_seconds: int = 3600) -> int:
```

Remove correlation entries older than the specified age. Returns the number of entries cleaned up.

### Lifecycle Methods

#### `start_consuming()`

```python
def start_consuming(self) -> None:
```

Start consuming messages. Blocks until stopped.

#### `stop_consuming()`

```python
def stop_consuming(self) -> None:
```

Stop consuming messages.

#### `close()`

```python
def close(self) -> None:
```

Close all resources (publisher, subscriber, channels).

## Message Properties

When handling messages, the `properties` dictionary contains:

- `routing_key`: The routing key of the message
- `correlation_id`: Correlation ID for request tracking
- `delivery_tag`: RabbitMQ delivery tag
- `app_id`: Name of the agent that sent the message

## Dead Letter Queue

### Automatic Setup

Each agent automatically gets:
- Main queue: `{agent_name}`
- Dead letter exchange: `{exchange_name}.dlx`
- Dead letter queue: `{agent_name}.dlq`

### Message Flow to DLQ

Messages are sent to the DLQ when:
1. Message handler raises an exception
2. Message is rejected with `requeue=False`
3. Message TTL expires (24 hours in DLQ)

### Monitoring DLQ

Use RabbitMQ Management UI to monitor DLQ:
- URL: http://localhost:15672
- Check queue: `{agent_name}.dlq`
- Inspect failed messages for debugging

## Best Practices

### 1. Implement Idempotent Handlers

Messages may be delivered multiple times. Ensure handlers are idempotent:

```python
def _handle_request(self, message, correlation_id):
    # Check if already processed
    if self._is_processed(correlation_id):
        logger.info(f"Already processed: {correlation_id}")
        return
    
    # Process message
    result = self._process(message)
    
    # Mark as processed
    self._mark_processed(correlation_id)
```

### 2. Clean Up Correlations

Always clean up correlation context when done:

```python
def _handle_final_response(self, message, correlation_id):
    try:
        # Process response
        self._process_response(message)
    finally:
        # Always clean up
        self.clear_correlation(correlation_id)
```

### 3. Use Context for Multi-Step Workflows

Store intermediate results in correlation context:

```python
# Step 1: Request data
correlation_id = self.publish_request(
    message=data_request,
    routing_key="data.request",
    reply_routing_key="data.response",
    context={"step": 1, "query": original_query}
)

# Step 2: Handle data response, request analysis
def _handle_data_response(self, message, correlation_id):
    context = self.get_correlation_context(correlation_id)
    
    # Update context for next step
    self.publish_request(
        message=analysis_request,
        routing_key="analysis.request",
        reply_routing_key="analysis.response",
        context={
            **context["context"],
            "step": 2,
            "data": message.data,
        }
    )
```

### 4. Handle Missing Context Gracefully

```python
def _handle_response(self, message, correlation_id):
    context = self.get_correlation_context(correlation_id)
    
    if not context:
        logger.warning(
            f"No context for correlation: {correlation_id}. "
            f"May be a duplicate or expired message."
        )
        return
    
    # Process with context
    self._process_with_context(message, context)
```

### 5. Log Correlation IDs

Always include correlation IDs in logs for tracing:

```python
logger.info(
    f"[{self.agent_name}] Processing request: "
    f"correlation_id={correlation_id}, "
    f"routing_key={routing_key}"
)
```

## Examples

See `examples/example_base_agent.py` for complete working examples of:
- Query Agent (multi-step workflow with correlation tracking)
- Data Retrieval Agent (request-response pattern)

## Related Documentation

- [Message Bus System](README.md)
- [Protocol Buffer Schemas](../../proto/README.md)
- [Connection Management](connection.py)
- [Publisher](publisher.py)
- [Subscriber](subscriber.py)

