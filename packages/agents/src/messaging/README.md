# Message Bus System

This module provides the message bus infrastructure for agent communication in the Chimera Analytics system. It includes connection management, channel handling, and publisher/subscriber patterns for RabbitMQ.

## Components

### Connection Management

- **ConnectionPool**: Manages RabbitMQ connections with automatic retry and exponential backoff
- **ChannelManager**: Handles channel creation, management, and recovery

### Messaging Patterns

- **BaseAgent**: Complete agent base class combining publisher and subscriber with correlation tracking
- **EventPublisher**: Base class for publishing messages to exchanges
- **EventSubscriber**: Abstract base class for consuming messages from queues
- **MessageBuilder**: Helper for creating message metadata

### Protocol Buffers

- Message schemas defined in `proto/messages.proto`
- Generated bindings in `messaging/generated/`
- Utilities for serialization/deserialization

## Features

### Connection Resilience

- Automatic reconnection with exponential backoff
- Configurable retry attempts and delays
- Connection health monitoring

### Message Routing

- Topic-based routing with flexible patterns
- Correlation ID tracking for request-response patterns
- Automatic context storage for multi-step workflows
- Dead letter queue (DLQ) for failed messages with 24-hour TTL

### Error Handling

- Automatic message acknowledgment
- Failed message routing to DLQ
- Comprehensive error logging

## Usage

### Recommended: Using BaseAgent

The `BaseAgent` class is the recommended way to create agents. It combines publisher and subscriber functionality with built-in correlation tracking:

```python
from typing import Dict, Any, Type
from messaging import BaseAgent, ConnectionPool
from messaging.generated import messages_pb2
from google.protobuf.message import Message as ProtoMessage

class MyAgent(BaseAgent):
    def __init__(self, connection_pool: ConnectionPool):
        super().__init__(
            connection_pool=connection_pool,
            agent_name="my_agent",
            routing_keys=["my_agent.request"],
        )
    
    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        return {
            "my_agent.request": messages_pb2.MyRequest,
        }
    
    def route_message(self, message, routing_key, properties):
        correlation_id = properties.get("correlation_id")
        if routing_key == "my_agent.request":
            self._handle_request(message, correlation_id)
    
    def _handle_request(self, message, correlation_id):
        # Process request
        response = messages_pb2.MyResponse()
        self.publish_response(response, "my_agent.response", correlation_id)

# Run agent
pool = ConnectionPool(config.rabbitmq)
agent = MyAgent(pool)
agent.start_consuming()
```

See [BaseAgent Documentation](BASE_AGENT.md) for complete guide and examples.

### Basic Publisher

```python
from messaging import ConnectionPool, EventPublisher
from messaging.generated import messages_pb2
from config import load_config

# Load configuration
config = load_config()

# Create connection pool
pool = ConnectionPool(config.rabbitmq)

# Create publisher
publisher = EventPublisher(
    connection_pool=pool,
    agent_name="my_agent",
    exchange_name="chimera.events"
)

# Create and publish message
request = messages_pb2.QueryRequest()
request.metadata.CopyFrom(create_metadata("my_agent"))
request.query = "What is the ZEC price?"

publisher.publish(request, routing_key="query.request")

# Cleanup
publisher.close()
pool.close()
```

### Basic Subscriber

```python
from typing import Dict, Any, Type
from messaging import ConnectionPool, EventSubscriber
from messaging.generated import messages_pb2
from google.protobuf.message import Message as ProtoMessage

class MyAgent(EventSubscriber):
    def __init__(self, connection_pool: ConnectionPool):
        super().__init__(
            connection_pool=connection_pool,
            agent_name="my_agent",
            routing_keys=["query.request"]
        )
    
    def get_message_class(self, routing_key: str) -> Type[ProtoMessage]:
        return messages_pb2.QueryRequest
    
    def handle_message(self, message: ProtoMessage, properties: Dict[str, Any]) -> None:
        print(f"Received: {message.query}")
        # Process message...

# Create and start agent
pool = ConnectionPool(config.rabbitmq)
agent = MyAgent(pool)
agent.start_consuming()  # Blocks until stopped
```

### Request-Response Pattern

```python
# Publisher side
publisher.publish_with_reply(
    message=request,
    routing_key="query.request",
    reply_queue="my_agent.replies",
    correlation_id="unique-id-123"
)

# Subscriber side - check correlation_id in properties
def handle_message(self, message, properties):
    correlation_id = properties.get("correlation_id")
    # Match with original request...
```

## Configuration

### Environment Variables

```bash
RABBITMQ__HOST=localhost
RABBITMQ__PORT=5672
RABBITMQ__USERNAME=guest
RABBITMQ__PASSWORD=guest
RABBITMQ__VHOST=/
```

### Connection Pool Options

```python
pool = ConnectionPool(
    config=rabbitmq_config,
    max_retries=5,              # Maximum retry attempts
    initial_retry_delay=1.0,    # Initial delay in seconds
    max_retry_delay=60.0        # Maximum delay in seconds
)
```

### Subscriber Options

```python
subscriber = EventSubscriber(
    connection_pool=pool,
    agent_name="my_agent",
    exchange_name="chimera.events",
    queue_name="my_agent_queue",     # Optional, defaults to agent_name
    routing_keys=["query.*"],        # Routing key patterns
    prefetch_count=1                 # QoS prefetch count
)
```

## Message Flow

### Standard Flow

1. Publisher creates message with metadata
2. Message serialized to Protocol Buffer format
3. Published to exchange with routing key
4. Exchange routes to bound queues
5. Subscriber receives and deserializes message
6. Message handler processes message
7. Message acknowledged (or rejected to DLQ)

### Dead Letter Queue Flow

1. Message processing fails
2. Message rejected with `requeue=False`
3. Message routed to DLX (Dead Letter Exchange)
4. Message stored in DLQ for manual inspection
5. TTL of 24 hours before automatic deletion

## Routing Keys

### Convention

Format: `<agent>.<action>`

Examples:
- `query.request` - Query agent request
- `query.response` - Query agent response
- `data.request` - Data retrieval request
- `data.response` - Data retrieval response
- `analysis.request` - Analysis request
- `analysis.response` - Analysis response

### Patterns

- `#` - Match zero or more words
- `*` - Match exactly one word
- `query.*` - Match all query agent messages
- `*.request` - Match all request messages

## Best Practices

### Publisher

1. Always include correlation IDs for request tracking
2. Use persistent messages for important data
3. Handle publish failures gracefully
4. Close publishers when done

### Subscriber

1. Implement idempotent message handlers
2. Keep message processing fast
3. Use appropriate prefetch counts
4. Handle all exceptions in message handlers
5. Log correlation IDs for debugging

### Error Handling

1. Let failed messages go to DLQ
2. Monitor DLQ for recurring issues
3. Implement retry logic in application layer
4. Log errors with full context

## Monitoring

### Key Metrics

- Connection status and uptime
- Message publish rate
- Message consume rate
- DLQ message count
- Processing errors

### Logging

All components log at appropriate levels:
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Failures requiring attention

## Testing

See `tests/test_messaging.py` for unit tests and examples.

## Troubleshooting

### Connection Failures

- Check RabbitMQ is running: `docker-compose ps`
- Verify credentials in configuration
- Check network connectivity
- Review connection logs

### Messages Not Received

- Verify queue bindings: RabbitMQ Management UI
- Check routing key patterns
- Confirm exchange exists
- Review subscriber logs

### Messages in DLQ

- Check subscriber error logs
- Verify message format
- Test message handler logic
- Consider message TTL

## Related Documentation

- [Protocol Buffer Schemas](../proto/README.md)
- [Agent Configuration](../config.py)
- [Example Agents](./examples/)
