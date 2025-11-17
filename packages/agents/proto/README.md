# Protocol Buffer Message Schemas

This directory contains Protocol Buffer definitions for all agent communication messages in the Chimera Analytics system.

## Schema File

- `messages.proto` - Complete message schema definitions for all agents

## Generating Bindings

### Python Bindings

To generate Python bindings:

```bash
# Unix/Linux/Mac
cd packages/agents
./scripts/generate_proto.sh

# Windows
cd packages/agents
.\scripts\generate_proto.ps1

# Or directly with Python
cd packages/agents
python scripts/generate_proto.py
```

Generated files will be placed in `packages/agents/src/messaging/generated/`

### TypeScript Bindings

To generate TypeScript bindings:

```bash
cd packages/api
npm run proto:generate
```

Generated files will be placed in `packages/api/src/messaging/generated/`

## Message Types

The schema defines messages for all agent interactions:

- **Query Agent**: `QueryRequest`, `QueryResponse`
- **Data Retrieval Agent**: `DataRetrievalRequest`, `DataRetrievalResponse`
- **Analysis Agent**: `AnalysisRequest`, `AnalysisResponse`
- **Narrative Agent**: `NarrativeRequest`, `NarrativeResponse`
- **Fact-Checker Agent**: `FactCheckRequest`, `FactCheckResponse`
- **Follow-up Agent**: `FollowUpRequest`, `FollowUpResponse`
- **Monitoring Agent**: `MonitoringEvent`, `AlertRule`
- **Common**: `ErrorResponse`, `MessageMetadata`

## Usage

### Python

```python
from messaging.generated import messages_pb2
from messaging.messages import create_metadata, serialize_message

# Create a query request
request = messages_pb2.QueryRequest()
request.metadata.CopyFrom(create_metadata("query_agent"))
request.user_id = "user123"
request.query = "What is the current ZEC price?"

# Serialize for transmission
data = serialize_message(request)
```

### TypeScript

```typescript
import { messages } from './messaging/generated/messages';
import { createMetadata } from './messaging/messages';

// Create a query request
const request = messages.chimera.messaging.QueryRequest.create({
  metadata: createMetadata('api_server'),
  userId: 'user123',
  query: 'What is the current ZEC price?'
});

// Serialize for transmission
const buffer = messages.chimera.messaging.QueryRequest.encode(request).finish();
```

## Updating Schemas

When modifying `messages.proto`:

1. Make your changes to the proto file
2. Regenerate bindings for both Python and TypeScript
3. Update any code that uses the modified messages
4. Run tests to ensure compatibility

## Best Practices

- Always include `MessageMetadata` in request/response messages
- Use correlation IDs to track request-response pairs
- Include timestamps for all messages
- Use appropriate data types (avoid string for numeric values)
- Document new message types and fields
