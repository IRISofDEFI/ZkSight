# Distributed Tracing with OpenTelemetry and Jaeger

This document explains how distributed tracing is implemented in the Chimera Analytics System using OpenTelemetry and Jaeger.

## Overview

Distributed tracing allows you to track requests as they flow through multiple agents and services. This is essential for:

- **Debugging**: Understanding the flow of requests and identifying where failures occur
- **Performance Analysis**: Identifying bottlenecks and slow operations
- **Dependency Mapping**: Visualizing how agents communicate
- **Root Cause Analysis**: Tracing errors back to their source

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────┐     Trace Context      ┌──────────────┐
│  API Server │ ──────────────────────▶ │ Query Agent  │
└──────┬──────┘     (via RabbitMQ)     └──────┬───────┘
       │                                       │
       │                                       ▼
       │                              ┌──────────────────┐
       │                              │ Data Retrieval   │
       │                              │     Agent        │
       │                              └──────┬───────────┘
       │                                     │
       ▼                                     ▼
┌─────────────┐                    ┌──────────────────┐
│   Jaeger    │◀───────────────────│ Analysis Agent   │
│  Collector  │                    └──────────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Jaeger    │
│     UI      │
└─────────────┘
```

## Components

### 1. OpenTelemetry SDK

OpenTelemetry provides the instrumentation for creating and propagating traces:

- **Tracer**: Creates spans for operations
- **Span**: Represents a single operation with timing and metadata
- **Context Propagation**: Passes trace context between services

### 2. Jaeger

Jaeger is the tracing backend that:

- Collects traces from all services
- Stores trace data
- Provides a UI for viewing and analyzing traces

### 3. OTLP Exporter

The OpenTelemetry Protocol (OTLP) exporter sends traces from agents to Jaeger using gRPC.

## Setup

### 1. Start Jaeger

Jaeger is included in the docker-compose.yml:

```bash
docker-compose up -d jaeger
```

Jaeger UI will be available at: http://localhost:16686

### 2. Configure Environment

Set the Jaeger endpoint in your environment:

```bash
# For agents (Python)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# For API (TypeScript)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 3. Initialize Tracing in Agents

In your agent startup code:

```python
from src.init_tracing import init_agent_tracing, shutdown_agent_tracing

# Initialize tracing before creating agents
init_agent_tracing(
    agent_name="query_agent",
    service_version="1.0.0",
    jaeger_endpoint="http://localhost:4317",
    enable_console_export=True,  # Optional: also log to console
)

# ... create and run agent ...

# Shutdown tracing on exit
shutdown_agent_tracing()
```

### 4. Initialize Tracing in API

Tracing is automatically initialized in the API server (see `packages/api/src/server.ts`).

## Usage

### Automatic Tracing

The following are automatically traced:

1. **HTTP Requests**: All API endpoints are traced
2. **Message Processing**: All agent message handlers are traced
3. **Database Operations**: MongoDB, InfluxDB, and Redis operations are traced
4. **External API Calls**: HTTP requests to external services are traced

### Manual Tracing

You can add custom tracing to your code:

#### Python (Agents)

```python
from src.tracing import (
    trace_agent_operation,
    set_span_attribute,
    add_span_event,
    traced_span,
)

# Using decorator
@trace_agent_operation("my_operation")
def my_function():
    set_span_attribute("custom.attribute", "value")
    add_span_event("processing.start")
    # ... do work ...
    add_span_event("processing.complete")

# Using context manager
with traced_span("database_query", attributes={"query": "SELECT *"}):
    # ... execute query ...
    pass
```

#### TypeScript (API)

```typescript
import {
  traceAsync,
  setSpanAttribute,
  addSpanEvent,
} from './tracing';

// Trace async function
await traceAsync(
  'process_request',
  async (span) => {
    span.setAttribute('user.id', userId);
    addSpanEvent('validation.start');
    // ... do work ...
    addSpanEvent('validation.complete');
  }
);
```

### Trace Context Propagation

Trace context is automatically propagated:

1. **HTTP → Agent**: API server injects trace context into RabbitMQ message headers
2. **Agent → Agent**: BaseAgent automatically extracts and injects trace context
3. **Agent → External API**: Trace context is injected into HTTP headers

## Viewing Traces

### Jaeger UI

1. Open http://localhost:16686
2. Select a service from the dropdown (e.g., "chimera-api", "query_agent")
3. Click "Find Traces"
4. Click on a trace to see the detailed view

### Trace Details

Each trace shows:

- **Service**: Which service handled each span
- **Operation**: What operation was performed
- **Duration**: How long each operation took
- **Tags**: Custom attributes added to spans
- **Events**: Events that occurred during the span
- **Logs**: Any logs associated with the span

### Example Trace

```
chimera-api: HTTP POST /api/queries [200ms]
  └─ query_agent: process_query [150ms]
      ├─ query_agent: nlp_processing [50ms]
      ├─ query_agent: entity_extraction [30ms]
      ├─ query_agent: intent_classification [40ms]
      └─ data_retrieval_agent: fetch_data [100ms]
          ├─ zcash_node: get_block_height [30ms]
          ├─ exchange_api: get_price [50ms]
          └─ redis: cache_set [5ms]
```

## Best Practices

### 1. Meaningful Span Names

Use descriptive names that indicate what the operation does:

```python
# Good
with traced_span("fetch_user_profile"):
    ...

# Bad
with traced_span("operation"):
    ...
```

### 2. Add Relevant Attributes

Add attributes that help with debugging:

```python
set_span_attribute("user.id", user_id)
set_span_attribute("query.type", "trend_analysis")
set_span_attribute("data_source.count", len(sources))
```

### 3. Record Important Events

Add events for significant milestones:

```python
add_span_event("validation.start")
add_span_event("cache.hit")
add_span_event("external_api.retry", {"attempt": 2})
```

### 4. Handle Errors Properly

Always record exceptions:

```python
try:
    # ... operation ...
except Exception as e:
    set_span_error(e)
    raise
```

### 5. Don't Over-Trace

Avoid creating spans for trivial operations:

```python
# Don't trace simple getters/setters
# Don't trace every loop iteration
# Focus on operations that cross service boundaries or take significant time
```

## Troubleshooting

### Traces Not Appearing

1. **Check Jaeger is running**:
   ```bash
   docker-compose ps jaeger
   ```

2. **Check endpoint configuration**:
   ```bash
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

3. **Check agent logs** for tracing initialization messages

4. **Verify network connectivity**:
   ```bash
   curl http://localhost:4317
   ```

### High Overhead

If tracing is causing performance issues:

1. **Reduce sampling rate** (not implemented yet, but can be added)
2. **Disable console export** in production
3. **Remove unnecessary custom spans**

### Missing Context Propagation

If traces are not connected across services:

1. **Verify headers are being passed** in message properties
2. **Check trace context extraction** in message handlers
3. **Ensure all services use the same propagator** (W3C Trace Context)

## Performance Impact

Tracing has minimal performance impact:

- **Span creation**: ~1-5 microseconds
- **Attribute addition**: ~0.5 microseconds
- **Context propagation**: ~2-3 microseconds
- **Export batching**: Asynchronous, no blocking

Total overhead: <1% for typical workloads

## Security Considerations

### Sensitive Data

Never include sensitive data in traces:

```python
# Bad
set_span_attribute("user.password", password)
set_span_attribute("api.key", api_key)

# Good
set_span_attribute("user.id", user_id)
set_span_attribute("api.key_prefix", api_key[:8])
```

### Access Control

Jaeger UI has no built-in authentication. In production:

1. Deploy Jaeger behind a reverse proxy with authentication
2. Use network policies to restrict access
3. Consider using Jaeger's OAuth proxy

## Advanced Topics

### Custom Exporters

You can add additional exporters (e.g., to send traces to multiple backends):

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin import ZipkinExporter

# Add Zipkin exporter
zipkin_exporter = ZipkinExporter(endpoint="http://zipkin:9411/api/v2/spans")
provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
```

### Sampling

To reduce trace volume in high-traffic scenarios:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
provider = TracerProvider(resource=resource, sampler=sampler)
```

### Custom Instrumentation

Create custom instrumentation for libraries:

```python
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

class MyLibraryInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self):
        return ["my-library >= 1.0"]
    
    def _instrument(self, **kwargs):
        # Add instrumentation hooks
        pass
    
    def _uninstrument(self, **kwargs):
        # Remove instrumentation hooks
        pass
```

## References

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry JavaScript Documentation](https://opentelemetry.io/docs/instrumentation/js/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
