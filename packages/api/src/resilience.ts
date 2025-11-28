/**
 * Resilience patterns for Chimera API.
 * 
 * This module provides retry logic with exponential backoff and circuit breaker
 * patterns for handling failures in external service calls.
 */
import { ChimeraError, ErrorCode, DataSourceError } from './errors';
import { logger } from './logging';

export enum CircuitState {
  CLOSED = 'closed',      // Normal operation
  OPEN = 'open',          // Failing, reject requests
  HALF_OPEN = 'half_open', // Testing if service recovered
}

export enum RetryStrategy {
  EXPONENTIAL = 'exponential',
  LINEAR = 'linear',
  CONSTANT = 'constant',
}

/**
 * Calculate exponential backoff delay
 */
export function exponentialBackoff(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 60000,
  jitter: boolean = true,
): number {
  let delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

  if (jitter) {
    // Add random jitter (±25%)
    const jitterAmount = delay * 0.25;
    delay = delay + (Math.random() * 2 - 1) * jitterAmount;
  }

  return Math.max(0, delay);
}

/**
 * Calculate linear backoff delay
 */
export function linearBackoff(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 60000,
): number {
  return Math.min(baseDelay * (attempt + 1), maxDelay);
}

/**
 * Return constant delay
 */
export function constantBackoff(delay: number = 1000): number {
  return delay;
}

export interface RetryConfig {
  maxAttempts: number;
  strategy: RetryStrategy;
  baseDelay: number;
  maxDelay: number;
  jitter: boolean;
  retryableErrors?: (new (...args: any[]) => Error)[];
}

/**
 * Retry a function with configurable backoff strategy
 */
export async function retry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {},
): Promise<T> {
  const {
    maxAttempts = 3,
    strategy = RetryStrategy.EXPONENTIAL,
    baseDelay = 1000,
    maxDelay = 60000,
    jitter = true,
    retryableErrors = [Error],
  } = config;

  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      const isRetryableType = retryableErrors.some(
        (ErrorClass) => error instanceof ErrorClass,
      );

      if (!isRetryableType) {
        throw error;
      }

      // Check if ChimeraError is marked as non-retryable
      if (error instanceof ChimeraError && !error.retryable) {
        throw error;
      }

      if (attempt < maxAttempts - 1) {
        let delay: number;
        if (strategy === RetryStrategy.EXPONENTIAL) {
          delay = exponentialBackoff(attempt, baseDelay, maxDelay, jitter);
        } else if (strategy === RetryStrategy.LINEAR) {
          delay = linearBackoff(attempt, baseDelay, maxDelay);
        } else {
          delay = constantBackoff(baseDelay);
        }

        logger.warn(`Attempt ${attempt + 1}/${maxAttempts} failed: ${error}. Retrying in ${delay}ms...`, {
          attempt: attempt + 1,
          maxAttempts,
          delay,
          error: error instanceof Error ? error.message : String(error),
        });

        await new Promise((resolve) => setTimeout(resolve, delay));
      } else {
        logger.error(`All ${maxAttempts} attempts failed. Last error: ${error}`, {
          maxAttempts,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }
  }

  throw lastError;
}

/**
 * Decorator for retry logic
 */
export function withRetry(config: Partial<RetryConfig> = {}) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      return retry(() => originalMethod.apply(this, args), config);
    };

    return descriptor;
  };
}

/**
 * Circuit breaker implementation
 */
export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime: Date | null = null;
  private successCount: number = 0;

  constructor(
    private readonly failureThreshold: number = 5,
    private readonly recoveryTimeout: number = 60000,
    private readonly expectedError: new (...args: any[]) => Error = Error,
    private readonly name: string = 'unnamed',
  ) {}

  getState(): CircuitState {
    return this.state;
  }

  getFailureCount(): number {
    return this.failureCount;
  }

  private shouldAttemptReset(): boolean {
    if (this.state !== CircuitState.OPEN) {
      return false;
    }

    if (!this.lastFailureTime) {
      return false;
    }

    const timeSinceFailure = Date.now() - this.lastFailureTime.getTime();
    return timeSinceFailure >= this.recoveryTimeout;
  }

  async call<T>(fn: () => Promise<T>): Promise<T> {
    // Check if we should attempt reset
    if (this.shouldAttemptReset()) {
      this.state = CircuitState.HALF_OPEN;
      this.successCount = 0;
      logger.info(`Circuit breaker '${this.name}' entering HALF_OPEN state`);
    }

    // Reject if circuit is open
    if (this.state === CircuitState.OPEN) {
      throw new DataSourceError(
        `Circuit breaker '${this.name}' is OPEN`,
        this.name,
        ErrorCode.DATA_SOURCE_UNAVAILABLE,
        true,
      );
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      if (error instanceof this.expectedError) {
        this.onFailure();
      }
      throw error;
    }
  }

  callSync<T>(fn: () => T): T {
    // Check if we should attempt reset
    if (this.shouldAttemptReset()) {
      this.state = CircuitState.HALF_OPEN;
      this.successCount = 0;
      logger.info(`Circuit breaker '${this.name}' entering HALF_OPEN state`);
    }

    // Reject if circuit is open
    if (this.state === CircuitState.OPEN) {
      throw new DataSourceError(
        `Circuit breaker '${this.name}' is OPEN`,
        this.name,
        ErrorCode.DATA_SOURCE_UNAVAILABLE,
        true,
      );
    }

    try {
      const result = fn();
      this.onSuccess();
      return result;
    } catch (error) {
      if (error instanceof this.expectedError) {
        this.onFailure();
      }
      throw error;
    }
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      // Require 2 successes to close circuit
      if (this.successCount >= 2) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
        logger.info(`Circuit breaker '${this.name}' closed after recovery`);
      }
    } else {
      // Reset failure count on success
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = new Date();

    if (this.state === CircuitState.HALF_OPEN) {
      // Failed during recovery, reopen circuit
      this.state = CircuitState.OPEN;
      logger.warn(`Circuit breaker '${this.name}' reopened after failed recovery`);
    } else if (this.failureCount >= this.failureThreshold) {
      // Too many failures, open circuit
      this.state = CircuitState.OPEN;
      logger.error(
        `Circuit breaker '${this.name}' opened after ${this.failureCount} failures`,
      );
    }
  }

  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = null;
    logger.info(`Circuit breaker '${this.name}' manually reset`);
  }
}

/**
 * Decorator for circuit breaker
 */
export function withCircuitBreaker(
  failureThreshold: number = 5,
  recoveryTimeout: number = 60000,
  name?: string,
) {
  const breaker = new CircuitBreaker(
    failureThreshold,
    recoveryTimeout,
    Error,
    name,
  );

  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      return breaker.call(() => originalMethod.apply(this, args));
    };

    // Attach breaker to method for manual control
    descriptor.value.circuitBreaker = breaker;

    return descriptor;
  };
}

/**
 * Global circuit breaker registry
 */
const circuitBreakers = new Map<string, CircuitBreaker>();

export function getCircuitBreaker(name: string): CircuitBreaker | undefined {
  return circuitBreakers.get(name);
}

export function registerCircuitBreaker(
  name: string,
  breaker: CircuitBreaker,
): void {
  circuitBreakers.set(name, breaker);
}

export function getAllCircuitBreakers(): Map<string, CircuitBreaker> {
  return new Map(circuitBreakers);
}

/**
 * Graceful degradation helper
 */
export async function withFallback<T>(
  primary: () => Promise<T>,
  fallback: () => Promise<T>,
  fallbackCondition?: (error: Error) => boolean,
): Promise<T> {
  try {
    return await primary();
  } catch (error) {
    const shouldFallback = fallbackCondition
      ? fallbackCondition(error as Error)
      : true;

    if (shouldFallback) {
      logger.warn('Primary operation failed, using fallback', {
        error: error instanceof Error ? error.message : String(error),
      });
      return await fallback();
    }

    throw error;
  }
}

/**
 * Timeout wrapper
 */
export async function withTimeout<T>(
  fn: () => Promise<T>,
  timeoutMs: number,
  timeoutError?: Error,
): Promise<T> {
  return Promise.race([
    fn(),
    new Promise<T>((_, reject) =>
      setTimeout(
        () =>
          reject(
            timeoutError ||
              new ChimeraError(
                `Operation timed out after ${timeoutMs}ms`,
                ErrorCode.DATA_SOURCE_TIMEOUT,
                true,
              ),
          ),
        timeoutMs,
      ),
    ),
  ]);
}
