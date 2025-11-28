/**
 * Example demonstrating structured logging usage in Chimera API.
 * 
 * This example shows how to:
 * 1. Set up structured logging
 * 2. Use correlation IDs
 * 3. Add context to logs
 * 4. Log different severity levels
 * 5. Log errors with stack traces
 */
import {
  createLogger,
  LogLevel,
  setCorrelationId,
  getCorrelationId,
  runWithCorrelationId,
  runWithCorrelationIdAsync,
  ContextLogger,
  createContextLogger,
  logRequestStart,
  logRequestEnd,
  logError,
  logAgentMessage,
  logDatabaseOperation,
  logCacheOperation,
  logExternalApiCall,
} from '../logging';

/**
 * Example 1: Basic structured logging
 */
function exampleBasicLogging(): void {
  console.log('\n=== Example 1: Basic Structured Logging ===\n');

  const logger = createLogger('example-api', LogLevel.INFO, true);

  // Log at different levels
  logger.debug('This is a debug message');
  logger.info('This is an info message');
  logger.warn('This is a warning message');
  logger.error('This is an error message');

  console.log('\n✅ Basic logging complete\n');
}

/**
 * Example 2: Using correlation IDs
 */
function exampleCorrelationId(): void {
  console.log('\n=== Example 2: Correlation ID Tracking ===\n');

  const logger = createLogger('example-api', LogLevel.INFO, true);

  // Set correlation ID for request tracking
  const correlationId = 'req-12345-abcde';
  setCorrelationId(correlationId);

  logger.info('Processing request');
  logger.info('Fetching data from database');
  logger.info('Request completed');

  // Get current correlation ID
  const currentId = getCorrelationId();
  console.log(`Current correlation ID: ${currentId}`);

  console.log('\n✅ Correlation ID example complete\n');
}

/**
 * Example 3: Running code with correlation ID
 */
function exampleRunWithCorrelationId(): void {
  console.log('\n=== Example 3: Run With Correlation ID ===\n');

  const logger = createLogger('example-api', LogLevel.INFO, true);

  // Run synchronous code with correlation ID
  runWithCorrelationId('sync-req-123', () => {
    logger.info('Inside sync context');
    logger.info('Correlation ID is automatically set');
  });

  console.log('\n✅ Run with correlation ID example complete\n');
}

/**
 * Example 4: Async code with correlation ID
 */
async function exampleAsyncCorrelationId(): Promise<void> {
  console.log('\n=== Example 4: Async Correlation ID ===\n');

  const logger = createLogger('example-api', LogLevel.INFO, true);

  // Run async code with correlation ID
  await runWithCorrelationIdAsync('async-req-456', async () => {
    logger.info('Inside async context');

    // Simulate async work
    await new Promise((resolve) => setTimeout(resolve, 100));

    logger.info('Async work completed');
  });

  console.log('\n✅ Async correlation ID example complete\n');
}

/**
 * Example 5: Using ContextLogger
 */
function exampleContextLogger(): void {
  console.log('\n=== Example 5: Context Logger ===\n');

  // Create logger with persistent context
  const logger = createContextLogger({
    service: 'api',
    version: '1.0.0',
  });

  // All logs will include service and version
  logger.info('API initialized');
  logger.info('Processing request', { request_id: 'req-123' });
  logger.info('Request completed', { duration_ms: 150 });

  // Create child logger with additional context
  const childLogger = logger.child({ user_id: 'user-456' });
  childLogger.info('User action', { action: 'login' });

  console.log('\n✅ Context logger example complete\n');
}

/**
 * Example 6: Request logging
 */
function exampleRequestLogging(): void {
  console.log('\n=== Example 6: Request Logging ===\n');

  const correlationId = 'req-789-xyz';
  const method = 'GET';
  const path = '/api/queries';

  // Log request start
  logRequestStart(method, path, correlationId);

  // Simulate request processing
  const startTime = Date.now();
  // ... processing ...
  const duration = Date.now() - startTime;

  // Log request end
  logRequestEnd(method, path, 200, duration, correlationId);

  console.log('\n✅ Request logging example complete\n');
}

/**
 * Example 7: Error logging
 */
function exampleErrorLogging(): void {
  console.log('\n=== Example 7: Error Logging ===\n');

  try {
    // Simulate an error
    throw new Error('Database connection failed');
  } catch (error) {
    // Log error with context
    logError(error as Error, {
      operation: 'database_connect',
      host: 'localhost',
      port: 27017,
      user_id: 'user-123',
    });
  }

  console.log('\n✅ Error logging example complete\n');
}

/**
 * Example 8: Agent message logging
 */
function exampleAgentMessageLogging(): void {
  console.log('\n=== Example 8: Agent Message Logging ===\n');

  const correlationId = 'msg-abc-123';

  // Log message sent to agent
  logAgentMessage('sent', 'QueryRequest', correlationId);

  // Simulate processing
  // ...

  // Log message received from agent
  logAgentMessage('received', 'QueryResponse', correlationId);

  console.log('\n✅ Agent message logging example complete\n');
}

/**
 * Example 9: Database operation logging
 */
function exampleDatabaseLogging(): void {
  console.log('\n=== Example 9: Database Operation Logging ===\n');

  // Log successful operation
  logDatabaseOperation('insert', 'users', 45, true);

  // Log failed operation
  logDatabaseOperation('update', 'queries', 120, false);

  console.log('\n✅ Database logging example complete\n');
}

/**
 * Example 10: Cache operation logging
 */
function exampleCacheLogging(): void {
  console.log('\n=== Example 10: Cache Operation Logging ===\n');

  logCacheOperation('hit', 'user:123:profile');
  logCacheOperation('miss', 'query:456:results');
  logCacheOperation('set', 'query:456:results');
  logCacheOperation('delete', 'user:123:session');

  console.log('\n✅ Cache logging example complete\n');
}

/**
 * Example 11: External API call logging
 */
function exampleExternalApiLogging(): void {
  console.log('\n=== Example 11: External API Call Logging ===\n');

  // Log successful API call
  logExternalApiCall('coinbase', '/v2/prices/ZEC-USD/spot', 234, 200);

  // Log failed API call
  const error = new Error('Connection timeout');
  logExternalApiCall('binance', '/api/v3/ticker/price', 5000, undefined, error);

  console.log('\n✅ External API logging example complete\n');
}

/**
 * Example 12: Multi-service tracing
 */
async function exampleMultiServiceTracing(): Promise<void> {
  console.log('\n=== Example 12: Multi-Service Tracing ===\n');

  const correlationId = 'trace-xyz-789';

  // Simulate request flowing through multiple services
  await runWithCorrelationIdAsync(correlationId, async () => {
    const apiLogger = createLogger('api-gateway', LogLevel.INFO, true);
    apiLogger.info('Request received at API gateway');

    // Simulate calling query service
    const queryLogger = createLogger('query-service', LogLevel.INFO, true);
    queryLogger.info('Processing query');

    await new Promise((resolve) => setTimeout(resolve, 50));

    // Simulate calling data service
    const dataLogger = createLogger('data-service', LogLevel.INFO, true);
    dataLogger.info('Fetching data');

    await new Promise((resolve) => setTimeout(resolve, 50));

    // Response
    apiLogger.info('Sending response');
  });

  console.log(`\n💡 All logs share correlation_id: ${correlationId}`);
  console.log('   Query in Grafana: {correlation_id="trace-xyz-789"}');
  console.log('\n✅ Multi-service tracing example complete\n');
}

/**
 * Example 13: Performance logging
 */
function examplePerformanceLogging(): void {
  console.log('\n=== Example 13: Performance Logging ===\n');

  const logger = createLogger('example-api', LogLevel.INFO, true);

  const operation = 'database_query';
  const startTime = Date.now();

  // Simulate work
  const result = Array.from({ length: 1000 }, (_, i) => i).reduce((a, b) => a + b, 0);

  const durationMs = Date.now() - startTime;

  logger.info('Operation completed', {
    operation,
    duration_ms: durationMs,
    success: true,
    rows_affected: 42,
    event: 'performance_metric',
  });

  // Log slow operation warning
  if (durationMs > 100) {
    logger.warn('Operation was slow', {
      operation,
      duration_ms: durationMs,
      threshold_ms: 100,
      event: 'slow_operation',
    });
  }

  console.log('\n✅ Performance logging example complete\n');
}

/**
 * Main function to run all examples
 */
async function main(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('Chimera Structured Logging Examples (TypeScript)');
  console.log('='.repeat(60));

  const examples = [
    { name: 'Basic Logging', fn: exampleBasicLogging },
    { name: 'Correlation ID', fn: exampleCorrelationId },
    { name: 'Run With Correlation ID', fn: exampleRunWithCorrelationId },
    { name: 'Async Correlation ID', fn: exampleAsyncCorrelationId },
    { name: 'Context Logger', fn: exampleContextLogger },
    { name: 'Request Logging', fn: exampleRequestLogging },
    { name: 'Error Logging', fn: exampleErrorLogging },
    { name: 'Agent Message Logging', fn: exampleAgentMessageLogging },
    { name: 'Database Logging', fn: exampleDatabaseLogging },
    { name: 'Cache Logging', fn: exampleCacheLogging },
    { name: 'External API Logging', fn: exampleExternalApiLogging },
    { name: 'Multi-Service Tracing', fn: exampleMultiServiceTracing },
    { name: 'Performance Logging', fn: examplePerformanceLogging },
  ];

  for (const example of examples) {
    try {
      const result = example.fn() as void | Promise<void>;
      if (result !== undefined && typeof (result as any).then === 'function') {
        await result;
      }
    } catch (error) {
      console.log(`\n❌ Example '${example.name}' failed: ${error}\n`);
    }
  }

  console.log('='.repeat(60));
  console.log('All examples complete!');
  console.log('='.repeat(60));
  console.log('\n📚 Next Steps:');
  console.log('   1. Start the log aggregation stack: docker-compose up -d');
  console.log('   2. Access Grafana: http://localhost:3000 (admin/admin)');
  console.log('   3. View logs in the "Chimera Application Logs" dashboard');
  console.log('   4. Try querying by correlation_id, service, or level');
  console.log('\n');
}

// Run examples if this file is executed directly
if (require.main === module) {
  main().catch((error) => {
    console.error('Failed to run examples:', error);
    process.exit(1);
  });
}

export {
  exampleBasicLogging,
  exampleCorrelationId,
  exampleRunWithCorrelationId,
  exampleAsyncCorrelationId,
  exampleContextLogger,
  exampleRequestLogging,
  exampleErrorLogging,
  exampleAgentMessageLogging,
  exampleDatabaseLogging,
  exampleCacheLogging,
  exampleExternalApiLogging,
  exampleMultiServiceTracing,
  examplePerformanceLogging,
};
