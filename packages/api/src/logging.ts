/**
 * Structured logging configuration for Chimera API.
 * 
 * This module provides JSON-formatted logging with correlation IDs and
 * configurable log levels for all API operations.
 */
import * as winston from 'winston';
import { AsyncLocalStorage } from 'async_hooks';

// AsyncLocalStorage for correlation ID
const correlationIdStorage = new AsyncLocalStorage<string>();

/**
 * Log levels
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

/**
 * Custom format for adding correlation ID
 */
const correlationIdFormat = winston.format((info) => {
  const correlationId = correlationIdStorage.getStore();
  if (correlationId) {
    info.correlation_id = correlationId;
  }
  return info;
});

/**
 * Create a Winston logger instance with structured JSON logging
 */
export function createLogger(
  serviceName: string = 'chimera-api',
  logLevel: LogLevel = LogLevel.INFO,
  jsonFormat: boolean = true,
): winston.Logger {
  const formats = [
    winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSSZ' }),
    correlationIdFormat(),
    winston.format.errors({ stack: true }),
  ];

  if (jsonFormat) {
    formats.push(
      winston.format.json(),
    );
  } else {
    formats.push(
      winston.format.printf(({ timestamp, level, message, ...meta }) => {
        const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
        return `${timestamp} [${level.toUpperCase()}]: ${message} ${metaStr}`;
      }),
    );
  }

  return winston.createLogger({
    level: logLevel,
    defaultMeta: { service: serviceName },
    format: winston.format.combine(...formats),
    transports: [
      new winston.transports.Console({
        format: jsonFormat
          ? winston.format.json()
          : winston.format.combine(
              winston.format.colorize(),
              winston.format.simple(),
            ),
      }),
    ],
  });
}

/**
 * Default logger instance
 */
export const logger = createLogger();

/**
 * Set correlation ID for the current async context
 */
export function setCorrelationId(correlationId: string): void {
  correlationIdStorage.enterWith(correlationId);
}

/**
 * Get correlation ID from the current async context
 */
export function getCorrelationId(): string | undefined {
  return correlationIdStorage.getStore();
}

/**
 * Run a function with a correlation ID
 */
export function runWithCorrelationId<T>(
  correlationId: string,
  fn: () => T,
): T {
  return correlationIdStorage.run(correlationId, fn);
}

/**
 * Run an async function with a correlation ID
 */
export async function runWithCorrelationIdAsync<T>(
  correlationId: string,
  fn: () => Promise<T>,
): Promise<T> {
  return correlationIdStorage.run(correlationId, fn);
}

/**
 * Logger with additional context
 */
export class ContextLogger {
  private logger: winston.Logger;
  private context: Record<string, any>;

  constructor(logger: winston.Logger, context: Record<string, any> = {}) {
    this.logger = logger;
    this.context = context;
  }

  private log(level: LogLevel, message: string, meta?: Record<string, any>): void {
    this.logger.log(level, message, { ...this.context, ...meta });
  }

  debug(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, meta);
  }

  info(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, meta);
  }

  warn(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, meta);
  }

  error(message: string, error?: Error, meta?: Record<string, any>): void {
    const errorMeta = error
      ? {
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
        }
      : {};
    this.log(LogLevel.ERROR, message, { ...errorMeta, ...meta });
  }

  child(additionalContext: Record<string, any>): ContextLogger {
    return new ContextLogger(this.logger, { ...this.context, ...additionalContext });
  }
}

/**
 * Create a context logger
 */
export function createContextLogger(
  context: Record<string, any> = {},
): ContextLogger {
  return new ContextLogger(logger, context);
}

/**
 * Helper functions for common logging patterns
 */

export function logRequestStart(
  method: string,
  path: string,
  correlationId: string,
): void {
  logger.info('Request started', {
    event: 'request_start',
    method,
    path,
    correlation_id: correlationId,
  });
}

export function logRequestEnd(
  method: string,
  path: string,
  statusCode: number,
  duration: number,
  correlationId: string,
): void {
  logger.info('Request completed', {
    event: 'request_end',
    method,
    path,
    status_code: statusCode,
    duration_ms: duration,
    correlation_id: correlationId,
  });
}

export function logError(
  error: Error,
  context?: Record<string, any>,
): void {
  logger.error('Error occurred', {
    event: 'error',
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
    ...context,
  });
}

export function logAgentMessage(
  direction: 'sent' | 'received',
  messageType: string,
  correlationId: string,
): void {
  logger.info(`Message ${direction}`, {
    event: `message_${direction}`,
    message_type: messageType,
    correlation_id: correlationId,
  });
}

export function logDatabaseOperation(
  operation: string,
  collection: string,
  duration: number,
  success: boolean,
): void {
  logger.info('Database operation', {
    event: 'database_operation',
    operation,
    collection,
    duration_ms: duration,
    success,
  });
}

export function logCacheOperation(
  operation: 'hit' | 'miss' | 'set' | 'delete',
  key: string,
): void {
  logger.debug('Cache operation', {
    event: 'cache_operation',
    operation,
    key,
  });
}

export function logExternalApiCall(
  service: string,
  endpoint: string,
  duration: number,
  statusCode?: number,
  error?: Error,
): void {
  const level = error ? LogLevel.ERROR : LogLevel.INFO;
  logger.log(level, 'External API call', {
    event: 'external_api_call',
    service,
    endpoint,
    duration_ms: duration,
    status_code: statusCode,
    error: error
      ? {
          name: error.name,
          message: error.message,
        }
      : undefined,
  });
}
