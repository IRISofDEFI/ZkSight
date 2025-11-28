/**
 * Example usage of error handling, logging, tracing, and resilience utilities.
 * 
 * This module demonstrates how to use the various error handling and resilience
 * patterns in the Chimera API.
 */
import {
  ChimeraError,
  ErrorCode,
  DataSourceError,
  QueryError,
  createErrorResponse,
} from '../errors';

import {
  createLogger,
  setCorrelationId,
  logError,
  logRequestStart,
  logRequestEnd,
} from '../logging';

import {
  setupTracing,
  traceAsync,
  traceSync,
  createSpan,
  SpanKind,
} from '../tracing';

import {
  retry,
  RetryStrategy,
  CircuitBreaker,
  withFallback,
  withTimeout,
} from '../resilience';

// Example 1: Basic error handling
function exampleErrorHandling(): void {
  try {
    // Raise a custom error
    throw new DataSourceError(
      'Failed to connect to Zcash node',
      'zcash-node',
      ErrorCode.DATA_SOURCE_UNAVAILABLE,
      true,
    );
  } catch (error) {
    if (error instanceof ChimeraError) {
      // Create standardized error response
      const errorResponse = createErrorResponse(error, 'req-123');
      console.log('Error response:', errorResponse);
    }
  }
}

// Example 2: Structured logging
function exampleLogging(): void {
  const logger = createLogger('example-api', 'info');
  
  // Set correlation ID
  setCorrelationId('corr-456');
  
  // Log request
  logRequestStart('GET', '/api/queries', 'corr-456');
  
  // Log with context
  logger.info('Processing query', {
    query_id: 'q-789',
    user_id: 'u-123',
    event: 'query_start',
  });
  
  // Log request end
  logRequestEnd('GET', '/api/queries', 200, 150, 'corr-456');
}

// Example 3: Distributed tracing
async function exampleTracing(): Promise<void> {
  setupTracing('example-api', '1.0.0', 'http://localhost:4317');
  
  // Trace an async operation
  await traceAsync(
    'fetch_data',
    async (span) => {
      span.setAttribute('source', 'api');
      // Simulate async work
      await new Promise((resolve) => setTimeout(resolve, 100));
      return { data: 'success' };
    },
    { operation: 'fetch' },
    SpanKind.CLIENT,
  );
  
  // Trace a sync operation
  const result = traceSync(
    'process_data',
    (span) => {
      span.setAttribute('items', 10);
      return { processed: 10 };
    },
  );
  
  console.log('Processed:', result);
}

// Example 4: Retry with exponential backoff
async function exampleRetry(): Promise<any> {
  let attempts = 0;
  
  return retry(
    async () => {
      attempts++;
      console.log(`Attempt ${attempts}`);
      
      // Simulate 70% failure rate
      if (Math.random() < 0.7) {
        throw new DataSourceError(
          'Temporary connection issue',
          'api',
          ErrorCode.DATA_SOURCE_UNAVAILABLE,
          true,
        );
      }
      
      return { status: 'success' };
    },
    {
      maxAttempts: 3,
      strategy: RetryStrategy.EXPONENTIAL,
      baseDelay: 1000,
      retryableErrors: [DataSourceError],
    },
  );
}

// Example 5: Circuit breaker
async function exampleCircuitBreaker(): Promise<void> {
  const breaker = new CircuitBreaker(5, 60000, Error, 'zcash-node');
  
  async function riskyOperation(): Promise<any> {
    // Simulate 30% failure rate
    if (Math.random() < 0.3) {
      throw new DataSourceError(
        'Node unavailable',
        'zcash-node',
        ErrorCode.DATA_SOURCE_UNAVAILABLE,
        true,
      );
    }
    return { block_height: 12345 };
  }
  
  // Make multiple calls
  for (let i = 0; i < 10; i++) {
    try {
      const result = await breaker.call(riskyOperation);
      console.log(`Call ${i + 1} succeeded:`, result);
    } catch (error) {
      console.log(`Call ${i + 1} failed:`, error instanceof Error ? error.message : error);
    }
    
    // Small delay between calls
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  
  console.log('Circuit state:', breaker.getState());
  console.log('Failure count:', breaker.getFailureCount());
}

// Example 6: Combining patterns
async function exampleCombined(): Promise<any> {
  const logger = createLogger('example-api');
  const breaker = new CircuitBreaker(5, 60000, Error, 'external-api');
  
  return traceAsync(
    'fetch_with_resilience',
    async (span) => {
      return retry(
        async () => {
          return breaker.call(async () => {
            // Simulate async operation
            await new Promise((resolve) => setTimeout(resolve, 100));
            
            logger.info('External API call successful', {
              event: 'api_call_success',
            });
            
            return { data: 'success' };
          });
        },
        {
          maxAttempts: 3,
          strategy: RetryStrategy.EXPONENTIAL,
        },
      );
    },
  );
}

// Example 7: Graceful degradation with fallback
async function exampleFallback(): Promise<any> {
  return withFallback(
    // Primary operation
    async () => {
      // Simulate failure
      throw new DataSourceError(
        'Primary source unavailable',
        'primary',
        ErrorCode.DATA_SOURCE_UNAVAILABLE,
        true,
      );
    },
    // Fallback operation
    async () => {
      console.log('Using fallback data source');
      return { data: 'fallback_data', source: 'cache' };
    },
    // Only fallback for specific errors
    (error) => error instanceof DataSourceError,
  );
}

// Example 8: Timeout handling
async function exampleTimeout(): Promise<any> {
  return withTimeout(
    async () => {
      // Simulate slow operation
      await new Promise((resolve) => setTimeout(resolve, 5000));
      return { data: 'success' };
    },
    2000, // 2 second timeout
    new ChimeraError(
      'Operation took too long',
      ErrorCode.DATA_SOURCE_TIMEOUT,
      true,
    ),
  );
}

// Run examples
async function runExamples(): Promise<void> {
  console.log('=== Error Handling Example ===');
  exampleErrorHandling();
  
  console.log('\n=== Logging Example ===');
  exampleLogging();
  
  console.log('\n=== Tracing Example ===');
  await exampleTracing();
  
  console.log('\n=== Retry Example ===');
  try {
    const result = await exampleRetry();
    console.log('Retry succeeded:', result);
  } catch (error) {
    console.log('Retry failed:', error);
  }
  
  console.log('\n=== Circuit Breaker Example ===');
  await exampleCircuitBreaker();
  
  console.log('\n=== Combined Patterns Example ===');
  try {
    const result = await exampleCombined();
    console.log('Combined operation succeeded:', result);
  } catch (error) {
    console.log('Combined operation failed:', error);
  }
  
  console.log('\n=== Fallback Example ===');
  try {
    const result = await exampleFallback();
    console.log('Fallback result:', result);
  } catch (error) {
    console.log('Fallback failed:', error);
  }
  
  console.log('\n=== Timeout Example ===');
  try {
    const result = await exampleTimeout();
    console.log('Timeout result:', result);
  } catch (error) {
    console.log('Timeout error:', error instanceof Error ? error.message : error);
  }
}

// Export for use in other modules
export {
  exampleErrorHandling,
  exampleLogging,
  exampleTracing,
  exampleRetry,
  exampleCircuitBreaker,
  exampleCombined,
  exampleFallback,
  exampleTimeout,
  runExamples,
};

// Run if executed directly
if (require.main === module) {
  runExamples().catch(console.error);
}
