# Query Agent

The Query Agent is responsible for processing natural language queries about Zcash data. It parses user questions, extracts relevant entities, classifies intent, manages conversation context, and routes requests to appropriate data sources.

## Components

### 1. NLP Pipeline (`nlp_pipeline.py`)

Processes natural language text using spaCy for linguistic analysis.

**Features:**
- Entity extraction (named entities, dates, numbers)
- Noun phrase extraction
- Token analysis (POS tagging, lemmatization)
- Sentence boundary detection
- Query structure analysis

**Usage:**
```python
from query.nlp_pipeline import NLPPipeline

nlp = NLPPipeline()
doc = nlp.process("What was the shielded transaction volume last week?")
entities = nlp.extract_entities(doc)
structure = nlp.analyze_query_structure(doc)
```

### 2. Entity Recognizer (`entity_recognizer.py`)

Extracts domain-specific entities from queries.

**Recognized Entities:**
- **Temporal**: Dates, time ranges (relative and absolute)
- **Metrics**: Zcash-specific metrics (shielded transactions, price, hash rate, etc.)
- **Zcash Terms**: Address types (Sprout, Sapling, Orchard), transaction types
- **Numeric**: Numbers, percentages, values with units

**Usage:**
```python
from query.entity_recognizer import EntityRecognizer

recognizer = EntityRecognizer()
entities = recognizer.recognize_entities(
    "What was the shielded transaction volume last 7 days?"
)
```

**Example Output:**
```python
[
    {
        "entity_type": "METRIC",
        "value": "shielded transaction",
        "confidence": 0.9,
        "canonical_name": "shielded_transactions"
    },
    {
        "entity_type": "TIME_RANGE",
        "value": "last 7 days",
        "confidence": 0.9,
        "resolved_range": {
            "start_timestamp": 1234567890000,
            "end_timestamp": 1234654290000
        }
    }
]
```

### 3. Intent Classifier (`intent_classifier.py`)

Classifies the user's intent from their query.

**Intent Types:**
- `TREND_ANALYSIS`: Analyzing changes over time
- `ANOMALY_DETECTION`: Finding unusual patterns or outliers
- `COMPARISON`: Comparing metrics or time periods
- `EXPLANATION`: Understanding causes and reasons
- `UNKNOWN`: Intent cannot be determined

**Usage:**
```python
from query.intent_classifier import IntentClassifier

classifier = IntentClassifier()
intent = classifier.classify(query, entities)
```

**Example Output:**
```python
{
    "intent_type": IntentType.TREND_ANALYSIS,
    "confidence": 0.85,
    "time_range": {
        "start_timestamp": 1234567890000,
        "end_timestamp": 1234654290000
    },
    "metrics": ["shielded_transactions"]
}
```

### 4. Context Manager (`context_manager.py`)

Manages conversation context across multiple queries in a session.

**Features:**
- Session-based context storage in Redis
- Query history tracking
- Context extraction and merging
- Automatic TTL-based cleanup

**Usage:**
```python
from query.context_manager import ContextManager
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
context_mgr = ContextManager(redis_client)

# Add query to history
context_mgr.add_query_to_history(
    session_id="session123",
    query="What was the price last week?",
    intent=intent,
    entities=entities
)

# Get context for current query
context = context_mgr.extract_context_for_query(
    session_id="session123",
    current_query="And this week?"
)
```

### 5. Clarification Engine (`clarification.py`)

Detects ambiguity and generates clarification questions.

**Ambiguity Detection:**
- Missing time range
- Missing metrics
- Ambiguous comparisons
- Unclear intent
- Low-confidence entities

**Usage:**
```python
from query.clarification import ClarificationEngine

clarification = ClarificationEngine()
result = clarification.check_for_ambiguity(
    query=query,
    intent=intent,
    entities=entities,
    context=context
)

if result["clarification_needed"]:
    for question in result["questions"]:
        print(question)
```

**Example Output:**
```python
{
    "clarification_needed": True,
    "questions": [
        "What time period are you interested in? (e.g., today, last week, last month)"
    ],
    "reasons": ["missing_time_range"]
}
```

### 6. Query Agent (`agent.py`)

Main agent that orchestrates all components and integrates with the message bus.

**Features:**
- Subscribes to query request events
- Processes queries through full pipeline
- Manages conversation context
- Publishes responses and data retrieval requests
- Handles errors gracefully

**Usage:**
```python
from query.agent import create_query_agent

# Create agent
agent = create_query_agent()

# Start listening for queries
agent.start()

# Process query directly (for testing)
result = agent.process_query(
    query="What was the shielded transaction volume last week?",
    user_id="user123",
    session_id="session456"
)
```

## Message Flow

```
User Query
    ↓
[Query Agent]
    ↓
1. NLP Processing (spaCy)
    ↓
2. Entity Recognition
    ↓
3. Intent Classification
    ↓
4. Context Retrieval
    ↓
5. Clarification Check
    ↓
6. Context Update
    ↓
Decision Point:
    ├─ Clarification Needed → Send QueryResponse with questions
    └─ Query Clear → Send DataRetrievalRequest + QueryResponse
```

## Running Examples

To see the Query Agent components in action:

```bash
cd packages/agents
python -m src.query.example
```

This will run demonstrations of:
- NLP pipeline processing
- Entity recognition
- Intent classification
- Clarification generation
- Full query processing pipeline

## Configuration

The Query Agent uses configuration from `AgentConfig`:

```python
from src.config import AgentConfig

config = AgentConfig(
    redis=RedisConfig(
        host="localhost",
        port=6379,
        db=0
    ),
    rabbitmq=RabbitMQConfig(
        host="localhost",
        port=5672,
        username="guest",
        password="guest"
    )
)
```

## Dependencies

Required packages:
- `spacy` - NLP processing
- `python-dateutil` - Date parsing
- `redis` - Context storage
- `pika` - RabbitMQ messaging
- `protobuf` - Message serialization

Install spaCy model:
```bash
python -m spacy download en_core_web_sm
```

## Testing

Run unit tests:
```bash
pytest tests/test_query_agent.py
```

## Integration with Other Agents

The Query Agent communicates with:

1. **Data Retrieval Agent**: Sends data retrieval requests with:
   - Required data sources (blockchain, exchange, social)
   - Time range
   - Metrics to fetch
   - Filters

2. **User Interface**: Sends query responses with:
   - Parsed intent
   - Extracted entities
   - Clarification questions (if needed)
   - Required data sources

## Future Enhancements

- [ ] Fine-tune BERT model for intent classification
- [ ] Add support for multi-turn clarification dialogs
- [ ] Implement query suggestion based on history
- [ ] Add support for complex nested queries
- [ ] Improve entity linking and disambiguation
- [ ] Add query validation and sanitization
- [ ] Implement query templates for common patterns
