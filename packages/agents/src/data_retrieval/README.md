# Data Retrieval Agent

The Data Retrieval Agent is responsible for fetching data from multiple sources including Zcash blockchain nodes, cryptocurrency exchanges, and social media platforms. It implements caching, storage, and message bus integration for the Chimera Analytics system.

## Features

### 1. Zcash Node RPC Client
- JSON-RPC client with connection pooling
- Fetches block data, transaction counts, and shielded pool metrics
- Exponential backoff retry logic
- Error handling and logging

### 2. Exchange API Integrations
- **Binance**: Market data, order books, recent trades
- **Coinbase**: Ticker data, order books, trade history
- **Kraken**: Market data with custom symbol mapping
- Rate limiting with token bucket algorithm
- Request queuing for API compliance

### 3. Social Data Collectors
- **Twitter**: Mention tracking with sentiment analysis
- **Reddit**: Community posts and sentiment from r/zec
- **GitHub**: Developer activity metrics (commits, PRs, issues)

### 4. Redis Caching Layer
- TTL-based caching for different data types:
  - On-chain data: 5 minutes
  - Market data: 1 minute
  - Social data: 15 minutes
- Cache key generation strategy
- Cache invalidation support

### 5. InfluxDB Storage
- Time series data models and measurement schemas
- Batch writing for performance
- Retention policies for data lifecycle management
- Query support with aggregation

### 6. Message Bus Integration
- Subscribes to `data_retrieval.request` events
- Publishes `data_retrieval.response` events
- Request correlation and error handling
- Dead letter queue support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Retrieval Agent                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Zcash Client │  │   Exchange   │  │    Social    │      │
│  │              │  │   Adapters   │  │   Clients    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  Cache Layer   │                        │
│                    │    (Redis)     │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │ Storage Layer  │                        │
│                    │  (InfluxDB)    │                        │
│                    └────────────────┘                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Message Bus   │
                    │   (RabbitMQ)   │
                    └────────────────┘
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Zcash Node RPC
ZCASH__HOST=localhost
ZCASH__PORT=8232
ZCASH__USERNAME=
ZCASH__PASSWORD=
ZCASH__USE_SSL=false

# Exchange APIs
BINANCE__API_KEY=your-binance-key
BINANCE__API_SECRET=your-binance-secret
COINBASE__API_KEY=your-coinbase-key
COINBASE__API_SECRET=your-coinbase-secret
KRAKEN__API_KEY=your-kraken-key
KRAKEN__API_SECRET=your-kraken-secret

# Social APIs
TWITTER__BEARER_TOKEN=your-twitter-token
REDDIT__CLIENT_ID=your-reddit-client-id
REDDIT__CLIENT_SECRET=your-reddit-secret
GITHUB__ACCESS_TOKEN=your-github-token
```

## Usage

### Basic Usage

```python
import asyncio
from chimera.config import load_config
from chimera.messaging.connection import ConnectionPool
from chimera.data_retrieval import DataRetrievalAgent, ZcashRPCConfig

async def main():
    config = load_config()
    connection_pool = ConnectionPool(config.rabbitmq)
    
    agent = DataRetrievalAgent(
        connection_pool=connection_pool,
        config=config,
        zcash_config=ZcashRPCConfig(host="localhost", port=8232)
    )
    
    await agent.initialize()
    agent.start_consuming()
    
    # Keep running
    await asyncio.Event().wait()

asyncio.run(main())
```

### Testing Individual Components

#### Zcash Client

```python
from chimera.data_retrieval import ZcashRPCClient, ZcashRPCConfig

async def test_zcash():
    config = ZcashRPCConfig(host="localhost", port=8232)
    
    async with ZcashRPCClient(config) as client:
        # Get blockchain info
        info = await client.get_blockchain_info()
        print(f"Chain: {info['chain']}")
        
        # Get current block
        height = await client.get_block_count()
        block = await client.get_block_data(height)
        print(f"Block {height}: {block.hash}")
        
        # Get shielded pool metrics
        pools = await client.get_shielded_pool_metrics()
        print(f"Total shielded: {pools.total_shielded_value} ZEC")
```

#### Exchange Adapters

```python
from chimera.data_retrieval.exchanges import BinanceAdapter

async def test_binance():
    async with BinanceAdapter() as exchange:
        # Get market data
        market = await exchange.get_market_data("ZEC/USDT")
        print(f"ZEC Price: ${market.price}")
        
        # Get order book
        book = await exchange.get_order_book("ZEC/USDT", depth=10)
        print(f"Spread: ${book.spread}")
```

#### Social Clients

```python
from chimera.data_retrieval.social import TwitterClient

async def test_twitter():
    async with TwitterClient(bearer_token="your-token") as client:
        # Search mentions
        mentions = await client.search_mentions(
            query="zcash OR $ZEC",
            max_results=100
        )
        print(f"Found {len(mentions)} mentions")
        
        # Get sentiment
        sentiment = await client.get_sentiment_summary(mentions)
        print(f"Average sentiment: {sentiment.average_sentiment}")
```

## Data Models

### Request Format

```python
{
    "request_id": "unique-request-id",
    "sources": ["zcash_node", "binance", "twitter"],
    "metrics": ["block_data", "price_ZEC_USD", "mentions"],
    "time_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-02T00:00:00Z"
    },
    "filters": {}
}
```

### Response Format

```python
{
    "request_id": "unique-request-id",
    "data": {
        "zcash_node": [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "metric": "block_height",
                "value": 2500000,
                "tags": {"source": "zcash_node", "metric_type": "network"}
            }
        ],
        "binance": [...]
    },
    "metadata": [
        {
            "source": "zcash_node",
            "timestamp": 1704110400,
            "cached": false
        }
    ],
    "errors": [],
    "cached": false
}
```

## Error Handling

The agent implements comprehensive error handling:

1. **Retry Logic**: Exponential backoff for transient failures
2. **Circuit Breaker**: Prevents cascading failures
3. **Graceful Degradation**: Continues with partial data if some sources fail
4. **Error Reporting**: Detailed error information in responses

## Performance

- **Connection Pooling**: Reuses HTTP connections for efficiency
- **Batch Writing**: Groups writes to InfluxDB for better performance
- **Caching**: Reduces redundant API calls
- **Rate Limiting**: Respects API rate limits automatically

## Monitoring

The agent logs important events:

- Data retrieval requests and responses
- Cache hits and misses
- API errors and retries
- Storage operations

## Testing

Run the example script:

```bash
cd packages/agents
python -m src.data_retrieval.example
```

## Dependencies

- `httpx`: Async HTTP client
- `redis`: Redis client for caching
- `influxdb-client`: InfluxDB client for storage
- `pydantic`: Data validation

## Future Enhancements

1. WebSocket support for real-time exchange data
2. Additional exchange integrations
3. More sophisticated sentiment analysis
4. Data quality validation
5. Automatic retry scheduling for failed requests
