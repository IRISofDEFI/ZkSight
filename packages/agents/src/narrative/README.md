# Narrative Agent

The Narrative Agent generates human-readable reports from analysis results using LLM integration.

## Features

- **LLM Integration**: OpenAI API client with streaming support
- **Report Generation**: Structured reports with executive summary and sections
- **Visualization Building**: Chart configurations for different visualization types
- **Report Storage**: MongoDB storage with TTL-based expiration
- **Export Formats**: JSON and HTML export

## Components

- `llm_client.py`: OpenAI API client
- `report_builder.py`: Builds structured reports from analysis results
- `visualization_builder.py`: Creates visualization configurations
- `storage.py`: MongoDB storage and export functionality
- `agent.py`: Main agent with message bus integration

## Usage

```python
from src.narrative.agent import NarrativeAgent
from src.messaging.connection import ConnectionPool
from src.config import load_config

config = load_config()
pool = ConnectionPool(config.rabbitmq)

agent = NarrativeAgent(
    connection_pool=pool,
    config=config,
)

agent.start_consuming()
```

## Configuration

Requires OpenAI API key in configuration:
```python
OPENAI__API_KEY=your-api-key
OPENAI__MODEL=gpt-4
OPENAI__TEMPERATURE=0.7
```

## Message Flow

- Subscribes to: `analysis.result`, `narrative.request`
- Publishes to: `narrative.generated`, `narrative.progress`

