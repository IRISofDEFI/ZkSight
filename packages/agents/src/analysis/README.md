# Analysis Agent

The Analysis Agent processes data from the Data Retrieval Agent and performs statistical analysis, anomaly detection, correlation analysis, and pattern recognition.

## Features

- **Statistical Analysis**: Mean, median, standard deviation, min/max calculations
- **Anomaly Detection**: Z-score based outlier detection
- **Correlation Analysis**: Pearson and Spearman correlation with significance testing
- **Pattern Recognition**: Moving averages, Bollinger Bands, change point detection
- **Significance Testing**: P-value calculations and confidence intervals

## Components

- `statistics_service.py`: Basic statistical calculations
- `anomaly_detector.py`: Z-score anomaly detection
- `correlation_service.py`: Correlation analysis with significance testing
- `pattern_detector.py`: Pattern recognition algorithms
- `significance_service.py`: Statistical significance testing
- `pipeline.py`: Orchestrates all analysis components
- `storage.py`: Persists analysis results to InfluxDB/MongoDB
- `agent.py`: Main agent with message bus integration

## Usage

```python
from src.analysis.agent import AnalysisAgent
from src.messaging.connection import ConnectionPool
from src.config import load_config

config = load_config()
pool = ConnectionPool(config.rabbitmq)

agent = AnalysisAgent(
    connection_pool=pool,
    config=config,
)

agent.start_consuming()
```

## Message Flow

- Subscribes to: `data_retrieval.response`, `analysis.request`
- Publishes to: `analysis.result`

