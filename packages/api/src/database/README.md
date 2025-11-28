# Database Layer

This directory contains database connection utilities and schema management for MongoDB and InfluxDB.

## Overview

The Chimera Analytics system uses two databases:
- **MongoDB**: Document store for user data, configurations, reports, and metadata
- **InfluxDB**: Time-series database for metrics and analytics data

## MongoDB

### Connection Management

```typescript
import { connectMongoDB, getMongoDB, closeMongoDB } from './database';

// Connect to MongoDB (automatically initializes collections and indexes)
const db = await connectMongoDB();

// Get existing connection
const db = getMongoDB();

// Close connection
await closeMongoDB();

// Health check
const isHealthy = await checkMongoDBHealth();
```

### Collections

All collections are automatically created with proper indexes on first connection:
- `users` - User profiles and authentication
- `dashboards` - Dashboard configurations
- `reports` - Generated reports (with TTL)
- `alert_rules` - Alert rule definitions
- `alert_history` - Alert trigger history
- `query_history` - Query execution history

See [models/README.md](../models/README.md) for detailed schema documentation.

## InfluxDB

### Connection Management

```typescript
import { 
  initializeInfluxDB, 
  getWriteApi, 
  getQueryApi,
  closeInfluxDB 
} from './database';

// Initialize connection
initializeInfluxDB({
  url: 'http://localhost:8086',
  token: 'your-token',
  org: 'chimera',
  bucket: 'zcash_metrics',
});

// Get APIs
const writeApi = getWriteApi();
const queryApi = getQueryApi();

// Close connection
await closeInfluxDB();
```

### Writing Metrics

```typescript
import { 
  writeMetric, 
  writeMetricsBatch,
  createMetricPoint,
  MetricType,
  DataSource,
  NetworkType 
} from './database';

// Write a single metric
await writeMetric(
  'block_height',
  2500000,
  MetricType.NETWORK,
  DataSource.NODE,
  NetworkType.MAINNET,
  { difficulty: 123456 }, // additional fields
  { pool: 'mining_pool_1' } // additional tags
);

// Write multiple metrics in batch
const points = [
  createMetricPoint('price', 45.67, MetricType.MARKET, DataSource.BINANCE),
  createMetricPoint('volume', 1234567, MetricType.MARKET, DataSource.BINANCE),
];
await writeMetricsBatch(points);

// Flush pending writes
await flushWrites();
```

### Measurement Schema

**Measurement**: `zcash_metrics`

**Tags** (indexed):
- `metric_type`: network | market | social
- `source`: node | binance | coinbase | kraken | twitter | reddit | github
- `network`: mainnet | testnet
- `metric_name`: Specific metric identifier

**Fields**:
- `value`: Primary metric value (float)
- `volume`: Optional volume data (float)
- `count`: Optional count data (integer)
- Additional custom fields as needed

**Timestamp**: Nanosecond precision

### Retention Policies

- **Hot Storage**: 1 year (365 days)
- **Cold Storage**: 3 years (1095 days)

### Downsampling

Continuous queries automatically downsample data:
- **Hourly**: Raw data → hourly aggregates (1 year retention)
- **Daily**: Hourly data → daily aggregates (3 years retention)

### Schema Setup

```typescript
import { setupInfluxDBSchema } from './database';

// Run once during initial setup (requires admin access)
await setupInfluxDBSchema({
  url: 'http://localhost:8086',
  token: 'admin-token',
  org: 'chimera',
  bucket: 'zcash_metrics',
});
```

This creates:
- Main bucket with 1-year retention
- `zcash_metrics_hourly` bucket
- `zcash_metrics_daily` bucket

## Environment Configuration

### MongoDB

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chimera
```

### InfluxDB

```env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=chimera
INFLUXDB_BUCKET=zcash_metrics
```

## Error Handling

Both database clients implement:
- Automatic reconnection with exponential backoff
- Connection pooling
- Timeout configuration
- Health checks

```typescript
// MongoDB health check
const mongoHealthy = await checkMongoDBHealth();

// InfluxDB health check
const influxHealthy = await checkInfluxDBHealth();
```

## Best Practices

### MongoDB

1. **Use typed collections** from `getCollections()`
2. **Leverage indexes** - all common queries are indexed
3. **Use projection** to limit returned fields
4. **Handle errors** - connection failures, duplicate keys, etc.
5. **Close connections** gracefully on shutdown

### InfluxDB

1. **Batch writes** for better performance
2. **Use appropriate tags** for efficient querying
3. **Flush writes** before shutdown
4. **Use downsampled data** for historical queries
5. **Monitor retention** and adjust as needed

## Performance Tuning

### MongoDB

- Connection pool: 2-10 connections
- Server selection timeout: 5 seconds
- Socket timeout: 45 seconds

### InfluxDB

- Batch size: 1000 points
- Flush interval: 10 seconds
- Max retries: 3
- Exponential backoff: base 2

## Monitoring

Monitor these metrics:
- Connection pool utilization
- Query execution time
- Write throughput
- Error rates
- Disk usage (especially InfluxDB)

## Troubleshooting

### MongoDB Connection Issues

```typescript
// Check connection
const db = getMongoDB();
await db.admin().ping();

// List collections
const collections = await db.listCollections().toArray();
```

### InfluxDB Write Issues

```typescript
// Check health
const health = await checkInfluxDBHealth();

// Verify bucket exists
const client = getClient();
const bucketsAPI = new BucketsAPI(client);
const buckets = await bucketsAPI.getBuckets();
```

## Migration

See [migrations/README.md](../migrations/README.md) for database migration documentation.
