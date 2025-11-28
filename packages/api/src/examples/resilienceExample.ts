/**
 * Example usage of resilience patterns (retry and circuit breaker).
 * 
 * This module demonstrates how to use retry logic and circuit breakers
 * to handle failures in external service calls.
 */
import {
  retry,
  RetryStrategy,
  CircuitBreaker,
  withCircuitBreaker,
  withFallback,
  withTimeout,
  registerCircuitBreaker,
} from '../resilience';
import { DataSourceError, ErrorCode } from '../errors';
import { logger } from '../logging';

// Example 1: Using retry function with exponential backoff
async function fetchDataFromAPI(url: string): Promise<Record<string, any>> {
  logger.info(`Fetching data from ${url}`);

  // Simulate API call that might fail
  if (Math.random() < 0.3) {
    // 30% chance of failure
    throw new DataSourceError(
      'API temporarily unavailable',
      url,
      ErrorCode.DATA_SOURCE_UNAVAILABLE,
      true,
    );
  }

  return { status: 'success', data: [1, 2, 3] };
}

async function fetchWithRetry(url: string): Promise<Record<string, any>> {
  return retry(() => fetchDataFromAPI(url), {
    maxAttempts: 3,
    strategy: RetryStrategy.EXPONENTIAL,
    baseDelay: 1000,
  });
}

// Example 2: Using circuit breaker class
const exchangeBreaker = new CircuitBreaker(5, 60000, Error, 'exchange_api');
registerCircuitBreaker('exchange_api', exchangeBreaker);

async function fetchExchangeData(
  exchange: string,
): Promise<Record<string, any>> {
  logger.info(`Fetching data from ${exchange}`);

  // Simulate API call
  if (Math.random() < 0.2) {
    // 20% chance of failure
    throw new DataSourceError(
      `Exchange ${exchange} API error`,
      exchange,
      ErrorCode.DATA_SOURCE_UNAVAILABLE,
      true,
    );
  }

  return { exchange, price: 100.0 };
}

async function fetchExchangeWithBreaker(
  exchange: string,
): Promise<Record<string, any>> {
  return exchangeBreaker.call(() => fetchExchangeData(exchange));
}

// Example 3: Using circuit breaker decorator
class DataRetriever {
  private breaker: CircuitBreaker;

  constructor() {
    this.breaker = new CircuitBreaker(3, 30000, Error, 'data_service');
    registerCircuitBreaker('data_service', this.breaker);
  }

  async fetchWithRetry(source: string): Promise<Record<string, any>> {
    return retry(() => this.breaker.call(() => this.fetchData(source)), {
      maxAttempts: 3,
      baseDelay: 500,
    });
  }

  private async fetchData(source: string): Promise<Record<string, any>> {
    logger.info(`Fetching from ${source}`);

    // Simulate API call
    if (Math.random() < 0.25) {
      // 25% chance of failure
      throw new DataSourceError(
        `Failed to fetch from ${source}`,
        source,
        ErrorCode.DATA_SOURCE_UNAVAILABLE,
        true,
      );
    }

    return { source, data: 'example' };
  }
}

// Example 4: Graceful degradation with fallback
async function fetchPrimaryData(): Promise<Record<string, any>> {
  logger.info('Fetching from primary source');

  // Simulate failure
  if (Math.random() < 0.5) {
    throw new DataSourceError(
      'Primary source unavailable',
      'primary',
      ErrorCode.DATA_SOURCE_UNAVAILABLE,
      true,
    );
  }

  return { source: 'primary', data: [1, 2, 3] };
}

async function fetchFallbackData(): Promise<Record<string, any>> {
  logger.info('Using fallback source');
  return { source: 'fallback', data: [4, 5, 6] };
}

async function fetchWithFallbackExample(): Promise<Record<string, any>> {
  return withFallback(
    fetchPrimaryData,
    fetchFallbackData,
    (error) => error instanceof DataSourceError,
  );
}

// Example 5: Using timeout wrapper
async function slowOperation(): Promise<string> {
  logger.info('Starting slow operation');
  await new Promise((resolve) => setTimeout(resolve, 5000));
  return 'completed';
}

async function fetchWithTimeout(): Promise<string> {
  return withTimeout(slowOperation, 2000); // 2 second timeout
}

// Example 6: Combining multiple patterns
async function robustFetch(url: string): Promise<Record<string, any>> {
  // Combine retry, circuit breaker, timeout, and fallback
  const breaker = new CircuitBreaker(3, 30000, Error, 'robust_fetch');

  const primaryFetch = async () => {
    return retry(
      () =>
        breaker.call(() =>
          withTimeout(
            () => fetchDataFromAPI(url),
            5000, // 5 second timeout
          ),
        ),
      {
        maxAttempts: 3,
        strategy: RetryStrategy.EXPONENTIAL,
        baseDelay: 1000,
      },
    );
  };

  const fallbackFetch = async () => {
    logger.warn('Using cached data as fallback');
    return { source: 'cache', data: [] };
  };

  return withFallback(primaryFetch, fallbackFetch);
}

// Main function to run examples
async function main() {
  console.log('=== Resilience Patterns Examples ===\n');

  // Example 1: Retry
  console.log('1. Retry with exponential backoff:');
  try {
    const result = await fetchWithRetry('https://api.example.com/data');
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed:', error, '\n');
  }

  // Example 2: Circuit breaker
  console.log('2. Circuit breaker:');
  try {
    const result = await fetchExchangeWithBreaker('binance');
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed:', error, '\n');
  }

  // Example 3: Combined retry and circuit breaker
  console.log('3. Combined retry and circuit breaker:');
  const retriever = new DataRetriever();
  try {
    const result = await retriever.fetchWithRetry('external_api');
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed:', error, '\n');
  }

  // Example 4: Graceful degradation
  console.log('4. Graceful degradation with fallback:');
  try {
    const result = await fetchWithFallbackExample();
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed:', error, '\n');
  }

  // Example 5: Timeout
  console.log('5. Timeout wrapper:');
  try {
    const result = await fetchWithTimeout();
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed: Operation timed out\n');
  }

  // Example 6: Robust fetch with all patterns
  console.log('6. Robust fetch (all patterns combined):');
  try {
    const result = await robustFetch('https://api.example.com/robust');
    console.log('   Success:', result, '\n');
  } catch (error) {
    console.log('   Failed:', error, '\n');
  }
}

// Run examples if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}

export {
  fetchWithRetry,
  fetchExchangeWithBreaker,
  DataRetriever,
  fetchWithFallbackExample,
  fetchWithTimeout,
  robustFetch,
};
