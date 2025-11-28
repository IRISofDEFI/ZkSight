import { InfluxDB, Point, WriteApi, QueryApi, HttpError } from '@influxdata/influxdb-client';
import { BucketsAPI, OrgsAPI } from '@influxdata/influxdb-client-apis';

/**
 * InfluxDB measurement schemas and utilities
 * Requirements: 2.1, 7.1, 11.1
 */

export interface InfluxDBConfig {
  url: string;
  token: string;
  org: string;
  bucket: string;
}

let influxDB: InfluxDB | null = null;
let writeApi: WriteApi | null = null;
let queryApi: QueryApi | null = null;

/**
 * Metric types for tagging
 */
export enum MetricType {
  NETWORK = 'network',
  MARKET = 'market',
  SOCIAL = 'social',
}

/**
 * Data source types
 */
export enum DataSource {
  NODE = 'node',
  BINANCE = 'binance',
  COINBASE = 'coinbase',
  KRAKEN = 'kraken',
  TWITTER = 'twitter',
  REDDIT = 'reddit',
  GITHUB = 'github',
}

/**
 * Network types
 */
export enum NetworkType {
  MAINNET = 'mainnet',
  TESTNET = 'testnet',
}

/**
 * Measurement name for all Zcash metrics
 */
export const ZCASH_METRICS_MEASUREMENT = 'zcash_metrics';

/**
 * Retention policy configurations
 * 1 year hot storage, 3 years cold storage
 */
export const RETENTION_POLICIES = {
  HOT: {
    name: 'hot_storage',
    duration: '365d', // 1 year
    shardDuration: '1d',
    replication: 1,
  },
  COLD: {
    name: 'cold_storage',
    duration: '1095d', // 3 years
    shardDuration: '7d',
    replication: 1,
  },
};

/**
 * Continuous query configurations for downsampling
 */
export const CONTINUOUS_QUERIES = [
  {
    name: 'downsample_hourly',
    query: `
      SELECT mean(value) as value, mean(volume) as volume, sum(count) as count
      INTO ${ZCASH_METRICS_MEASUREMENT}_hourly
      FROM ${ZCASH_METRICS_MEASUREMENT}
      GROUP BY time(1h), metric_type, source, network
    `,
    interval: '1h',
  },
  {
    name: 'downsample_daily',
    query: `
      SELECT mean(value) as value, mean(volume) as volume, sum(count) as count
      INTO ${ZCASH_METRICS_MEASUREMENT}_daily
      FROM ${ZCASH_METRICS_MEASUREMENT}_hourly
      GROUP BY time(1d), metric_type, source, network
    `,
    interval: '1d',
  },
];

/**
 * Initialize InfluxDB connection
 */
export function initializeInfluxDB(config: InfluxDBConfig): void {
  influxDB = new InfluxDB({
    url: config.url,
    token: config.token,
  });

  writeApi = influxDB.getWriteApi(config.org, config.bucket, 'ns', {
    batchSize: 1000,
    flushInterval: 10000,
    maxRetries: 3,
    maxRetryDelay: 15000,
    exponentialBase: 2,
  });

  queryApi = influxDB.getQueryApi(config.org);

  console.log('InfluxDB initialized');
}

/**
 * Get write API instance
 */
export function getWriteApi(): WriteApi {
  if (!writeApi) {
    throw new Error('InfluxDB not initialized. Call initializeInfluxDB() first.');
  }
  return writeApi;
}

/**
 * Get query API instance
 */
export function getQueryApi(): QueryApi {
  if (!queryApi) {
    throw new Error('InfluxDB not initialized. Call initializeInfluxDB() first.');
  }
  return queryApi;
}

/**
 * Create a data point for zcash_metrics measurement
 */
export function createMetricPoint(
  metricName: string,
  value: number,
  metricType: MetricType,
  source: DataSource,
  network: NetworkType = NetworkType.MAINNET,
  additionalFields?: Record<string, number>,
  additionalTags?: Record<string, string>,
  timestamp?: Date
): Point {
  const point = new Point(ZCASH_METRICS_MEASUREMENT)
    .tag('metric_type', metricType)
    .tag('source', source)
    .tag('network', network)
    .tag('metric_name', metricName)
    .floatField('value', value);

  // Add optional fields
  if (additionalFields) {
    for (const [key, val] of Object.entries(additionalFields)) {
      if (typeof val === 'number') {
        if (Number.isInteger(val)) {
          point.intField(key, val);
        } else {
          point.floatField(key, val);
        }
      }
    }
  }

  // Add optional tags
  if (additionalTags) {
    for (const [key, val] of Object.entries(additionalTags)) {
      point.tag(key, val);
    }
  }

  // Set timestamp if provided
  if (timestamp) {
    point.timestamp(timestamp);
  }

  return point;
}

/**
 * Write a single metric point
 */
export async function writeMetric(
  metricName: string,
  value: number,
  metricType: MetricType,
  source: DataSource,
  network: NetworkType = NetworkType.MAINNET,
  additionalFields?: Record<string, number>,
  additionalTags?: Record<string, string>,
  timestamp?: Date
): Promise<void> {
  const api = getWriteApi();
  const point = createMetricPoint(
    metricName,
    value,
    metricType,
    source,
    network,
    additionalFields,
    additionalTags,
    timestamp
  );
  api.writePoint(point);
}

/**
 * Write multiple metric points in batch
 */
export async function writeMetricsBatch(points: Point[]): Promise<void> {
  const api = getWriteApi();
  api.writePoints(points);
}

/**
 * Flush pending writes
 */
export async function flushWrites(): Promise<void> {
  if (writeApi) {
    await writeApi.flush();
  }
}

/**
 * Close InfluxDB connection
 */
export async function closeInfluxDB(): Promise<void> {
  if (writeApi) {
    await writeApi.close();
    writeApi = null;
  }
  influxDB = null;
  queryApi = null;
  console.log('InfluxDB connection closed');
}

/**
 * Setup retention policies and continuous queries
 * Note: This requires admin access and should be run during initial setup
 */
export async function setupInfluxDBSchema(config: InfluxDBConfig): Promise<void> {
  if (!influxDB) {
    throw new Error('InfluxDB not initialized');
  }

  try {
    const orgsAPI = new OrgsAPI(influxDB);
    const bucketsAPI = new BucketsAPI(influxDB);

    // Get organization
    const orgs = await orgsAPI.getOrgs({ org: config.org });
    if (!orgs.orgs || orgs.orgs.length === 0) {
      throw new Error(`Organization ${config.org} not found`);
    }
    const orgID = orgs.orgs[0].id;

    // Check if bucket exists
    const buckets = await bucketsAPI.getBuckets({ orgID, name: config.bucket });
    
    if (!buckets.buckets || buckets.buckets.length === 0) {
      // Create bucket with hot storage retention
      await bucketsAPI.postBuckets({
        body: {
          orgID,
          name: config.bucket,
          retentionRules: [
            {
              type: 'expire',
              everySeconds: 365 * 24 * 60 * 60, // 1 year
            },
          ],
        },
      });
      console.log(`Created bucket: ${config.bucket}`);
    }

    // Create additional buckets for downsampled data
    const downsampledBuckets = [
      { name: `${config.bucket}_hourly`, retention: 365 * 24 * 60 * 60 },
      { name: `${config.bucket}_daily`, retention: 3 * 365 * 24 * 60 * 60 },
    ];

    for (const { name, retention } of downsampledBuckets) {
      const existing = await bucketsAPI.getBuckets({ orgID, name });
      if (!existing.buckets || existing.buckets.length === 0) {
        await bucketsAPI.postBuckets({
          body: {
            orgID,
            name,
            retentionRules: [
              {
                type: 'expire',
                everySeconds: retention,
              },
            ],
          },
        });
        console.log(`Created bucket: ${name}`);
      }
    }

    console.log('InfluxDB schema setup completed');
  } catch (error) {
    if (error instanceof HttpError) {
      console.error('InfluxDB setup error:', error.statusCode, error.statusMessage);
    } else {
      console.error('InfluxDB setup error:', error);
    }
    throw error;
  }
}

/**
 * Health check for InfluxDB connection
 */
export async function checkInfluxDBHealth(): Promise<boolean> {
  if (!influxDB) {
    return false;
  }

  try {
    const health = await influxDB.health();
    return health.status === 'pass';
  } catch (error) {
    console.error('InfluxDB health check failed:', error);
    return false;
  }
}
