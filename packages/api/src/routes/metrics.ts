/**
 * Metrics data endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';
import { InfluxDB, QueryApi } from '@influxdata/influxdb-client';
import { AuthMiddleware } from '../auth';
import { ApiError } from '../middleware/errorHandler';
import { Config } from '../config';

export interface MetricQuery {
  metric: string;
  timeRange: {
    start: string | Date;
    end?: string | Date;
  };
  aggregation?: 'mean' | 'sum' | 'min' | 'max' | 'count';
  interval?: string;
  filters?: Record<string, string>;
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  tags?: Record<string, string>;
}

export class MetricsRoutes {
  private router: Router;
  private authMiddleware: AuthMiddleware;
  private influxDB: InfluxDB;
  private queryApi: QueryApi;
  private bucket: string;
  private org: string;

  constructor(
    authMiddleware: AuthMiddleware,
    config: Config
  ) {
    this.router = Router();
    this.authMiddleware = authMiddleware;
    
    // Initialize InfluxDB client
    // Note: InfluxDB config should be added to Config type
    const influxUrl = process.env.INFLUXDB_URL || 'http://localhost:8086';
    const influxToken = process.env.INFLUXDB_TOKEN || '';
    this.org = process.env.INFLUXDB_ORG || 'chimera';
    this.bucket = process.env.INFLUXDB_BUCKET || 'metrics';
    
    this.influxDB = new InfluxDB({ url: influxUrl, token: influxToken });
    this.queryApi = this.influxDB.getQueryApi(this.org);
    
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Query metrics
    this.router.get(
      '/',
      this.authMiddleware.authenticate,
      this.queryMetrics.bind(this)
    );

    // Export metrics data
    this.router.get(
      '/export',
      this.authMiddleware.authenticate,
      this.exportMetrics.bind(this)
    );

    // Get available metrics
    this.router.get(
      '/available',
      this.authMiddleware.authenticate,
      this.getAvailableMetrics.bind(this)
    );
  }

  /**
   * GET /api/metrics - Query metrics with time range and aggregation
   */
  private async queryMetrics(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const {
        metric,
        start,
        end,
        aggregation,
        interval,
        ...filters
      } = req.query as any;

      if (!metric) {
        throw this.createValidationError('Metric name is required');
      }

      if (!start) {
        throw this.createValidationError('Start time is required');
      }

      // Build Flux query
      const fluxQuery = this.buildFluxQuery({
        metric,
        timeRange: { start, end },
        aggregation,
        interval,
        filters,
      });

      // Execute query
      const data: MetricDataPoint[] = [];
      
      await new Promise<void>((resolve, reject) => {
        this.queryApi.queryRows(fluxQuery, {
          next: (row, tableMeta) => {
            const record = tableMeta.toObject(row);
            data.push({
              timestamp: record._time,
              value: record._value,
              tags: this.extractTags(record),
            });
          },
          error: (error) => {
            console.error('InfluxDB query error:', error);
            reject(error);
          },
          complete: () => {
            resolve();
          },
        });
      });

      res.json({
        metric,
        timeRange: { start, end },
        aggregation,
        interval,
        data,
        count: data.length,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/metrics/export - Export metrics data
   */
  private async exportMetrics(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const {
        metric,
        start,
        end,
        format = 'json',
        ...filters
      } = req.query as any;

      if (!metric) {
        throw this.createValidationError('Metric name is required');
      }

      if (!start) {
        throw this.createValidationError('Start time is required');
      }

      // Build Flux query
      const fluxQuery = this.buildFluxQuery({
        metric,
        timeRange: { start, end },
        filters,
      });

      // Execute query
      const data: MetricDataPoint[] = [];
      
      await new Promise<void>((resolve, reject) => {
        this.queryApi.queryRows(fluxQuery, {
          next: (row, tableMeta) => {
            const record = tableMeta.toObject(row);
            data.push({
              timestamp: record._time,
              value: record._value,
              tags: this.extractTags(record),
            });
          },
          error: (error) => {
            console.error('InfluxDB query error:', error);
            reject(error);
          },
          complete: () => {
            resolve();
          },
        });
      });

      // Export based on format
      if (format === 'csv') {
        const csv = this.convertToCSV(data);
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader(
          'Content-Disposition',
          `attachment; filename="metrics-${metric}-${Date.now()}.csv"`
        );
        res.send(csv);
      } else {
        res.setHeader('Content-Type', 'application/json');
        res.setHeader(
          'Content-Disposition',
          `attachment; filename="metrics-${metric}-${Date.now()}.json"`
        );
        res.json(data);
      }
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/metrics/available - Get list of available metrics
   */
  private async getAvailableMetrics(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      // Query to get unique metric names
      const fluxQuery = `
        from(bucket: "${this.bucket}")
          |> range(start: -30d)
          |> group(columns: ["_measurement"])
          |> distinct(column: "_measurement")
          |> keep(columns: ["_value"])
      `;

      const metrics: string[] = [];
      
      await new Promise<void>((resolve, reject) => {
        this.queryApi.queryRows(fluxQuery, {
          next: (row, tableMeta) => {
            const record = tableMeta.toObject(row);
            if (record._value) {
              metrics.push(record._value);
            }
          },
          error: (error) => {
            console.error('InfluxDB query error:', error);
            reject(error);
          },
          complete: () => {
            resolve();
          },
        });
      });

      res.json({
        metrics: metrics.sort(),
        count: metrics.length,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Build Flux query from parameters
   */
  private buildFluxQuery(query: MetricQuery): string {
    const { metric, timeRange, aggregation, interval, filters } = query;

    let fluxQuery = `
      from(bucket: "${this.bucket}")
        |> range(start: ${this.formatTime(timeRange.start)}${
      timeRange.end ? `, stop: ${this.formatTime(timeRange.end)}` : ''
    })
        |> filter(fn: (r) => r._measurement == "${metric}")
    `;

    // Add filters
    if (filters) {
      for (const [key, value] of Object.entries(filters)) {
        fluxQuery += `\n        |> filter(fn: (r) => r.${key} == "${value}")`;
      }
    }

    // Add aggregation
    if (aggregation && interval) {
      const aggFunction = this.getAggregationFunction(aggregation);
      fluxQuery += `\n        |> aggregateWindow(every: ${interval}, fn: ${aggFunction}, createEmpty: false)`;
    } else if (aggregation) {
      const aggFunction = this.getAggregationFunction(aggregation);
      fluxQuery += `\n        |> ${aggFunction}()`;
    }

    fluxQuery += `\n        |> yield(name: "result")`;

    return fluxQuery;
  }

  /**
   * Format time for Flux query
   */
  private formatTime(time: string | Date): string {
    if (typeof time === 'string') {
      // Check if it's a relative time (e.g., "-1h", "-7d")
      if (time.startsWith('-')) {
        return time;
      }
      // Otherwise treat as ISO timestamp
      return new Date(time).toISOString();
    }
    return time.toISOString();
  }

  /**
   * Get Flux aggregation function name
   */
  private getAggregationFunction(aggregation: string): string {
    const map: Record<string, string> = {
      mean: 'mean',
      sum: 'sum',
      min: 'min',
      max: 'max',
      count: 'count',
    };
    return map[aggregation] || 'mean';
  }

  /**
   * Extract tags from InfluxDB record
   */
  private extractTags(record: any): Record<string, string> {
    const tags: Record<string, string> = {};
    const excludeKeys = ['_time', '_value', '_field', '_measurement', 'result', 'table'];
    
    for (const [key, value] of Object.entries(record)) {
      if (!excludeKeys.includes(key) && typeof value === 'string') {
        tags[key] = value;
      }
    }
    
    return tags;
  }

  /**
   * Convert data to CSV format
   */
  private convertToCSV(data: MetricDataPoint[]): string {
    if (data.length === 0) {
      return 'timestamp,value\n';
    }

    // Get all unique tag keys
    const tagKeys = new Set<string>();
    data.forEach((point) => {
      if (point.tags) {
        Object.keys(point.tags).forEach((key) => tagKeys.add(key));
      }
    });

    // Build header
    const headers = ['timestamp', 'value', ...Array.from(tagKeys)];
    let csv = headers.join(',') + '\n';

    // Build rows
    data.forEach((point) => {
      const row = [
        point.timestamp,
        point.value,
        ...Array.from(tagKeys).map((key) => point.tags?.[key] || ''),
      ];
      csv += row.join(',') + '\n';
    });

    return csv;
  }

  private createValidationError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 400;
    error.code = 'INVALID_REQUEST';
    error.retryable = false;
    return error;
  }

  getRouter(): Router {
    return this.router;
  }
}
