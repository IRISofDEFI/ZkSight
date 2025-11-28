/**
 * Tests for resilience patterns (retry and circuit breaker).
 */
import { describe, it, expect, vi } from 'vitest';
import {
  exponentialBackoff,
  linearBackoff,
  constantBackoff,
  retry,
  RetryStrategy,
  CircuitBreaker,
  CircuitState,
  withRetry,
  withCircuitBreaker,
  withFallback,
  withTimeout,
} from './resilience';
import { ChimeraError, ErrorCode, DataSourceError } from './errors';

describe('Exponential Backoff', () => {
  it('should increase delay exponentially', () => {
    const delay0 = exponentialBackoff(0, 1000, 60000, false);
    const delay1 = exponentialBackoff(1, 1000, 60000, false);
    const delay2 = exponentialBackoff(2, 1000, 60000, false);

    expect(delay0).toBe(1000);
    expect(delay1).toBe(2000);
    expect(delay2).toBe(4000);
  });

  it('should respect max delay', () => {
    const delay = exponentialBackoff(10, 1000, 10000, false);
    expect(delay).toBe(10000);
  });

  it('should add jitter when enabled', () => {
    const delays = Array.from({ length: 10 }, () =>
      exponentialBackoff(1, 1000, 60000, true),
    );

    // All delays should be different due to jitter
    const uniqueDelays = new Set(delays);
    expect(uniqueDelays.size).toBeGreaterThan(1);

    // All delays should be within reasonable range (2000 ± 25%)
    delays.forEach((delay) => {
      expect(delay).toBeGreaterThanOrEqual(1500);
      expect(delay).toBeLessThanOrEqual(2500);
    });
  });
});

describe('Linear Backoff', () => {
  it('should increase delay linearly', () => {
    const delay0 = linearBackoff(0, 1000);
    const delay1 = linearBackoff(1, 1000);
    const delay2 = linearBackoff(2, 1000);

    expect(delay0).toBe(1000);
    expect(delay1).toBe(2000);
    expect(delay2).toBe(3000);
  });

  it('should respect max delay', () => {
    const delay = linearBackoff(100, 1000, 10000);
    expect(delay).toBe(10000);
  });
});

describe('Constant Backoff', () => {
  it('should return same value', () => {
    const delay = constantBackoff(5000);
    expect(delay).toBe(5000);
  });
});

describe('Retry Function', () => {
  it('should succeed on first attempt', async () => {
    const mockFn = vi.fn().mockResolvedValue('success');

    const result = await retry(mockFn);

    expect(result).toBe('success');
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('should retry and eventually succeed', async () => {
    const mockFn = vi
      .fn()
      .mockRejectedValueOnce(new Error('fail'))
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValue('success');

    const result = await retry(mockFn, {
      maxAttempts: 3,
      baseDelay: 10,
    });

    expect(result).toBe('success');
    expect(mockFn).toHaveBeenCalledTimes(3);
  });

  it('should exhaust attempts and throw', async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error('fail'));

    await expect(
      retry(mockFn, {
        maxAttempts: 3,
        baseDelay: 10,
      }),
    ).rejects.toThrow('fail');

    expect(mockFn).toHaveBeenCalledTimes(3);
  });

  it('should not retry non-retryable errors', async () => {
    const error = new ChimeraError(
      'non-retryable',
      ErrorCode.INVALID_QUERY,
      false,
    );
    const mockFn = vi.fn().mockRejectedValue(error);

    await expect(
      retry(mockFn, {
        maxAttempts: 3,
        retryableErrors: [ChimeraError],
      }),
    ).rejects.toThrow(error);

    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('should use exponential backoff strategy', async () => {
    const mockFn = vi
      .fn()
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValue('success');

    const startTime = Date.now();
    await retry(mockFn, {
      maxAttempts: 2,
      strategy: RetryStrategy.EXPONENTIAL,
      baseDelay: 100,
      jitter: false,
    });
    const duration = Date.now() - startTime;

    // Should have waited ~100ms
    expect(duration).toBeGreaterThanOrEqual(90);
    expect(duration).toBeLessThan(200);
  });
});

describe('Circuit Breaker', () => {
  it('should start in CLOSED state', () => {
    const breaker = new CircuitBreaker(3);

    expect(breaker.getState()).toBe(CircuitState.CLOSED);
    expect(breaker.getFailureCount()).toBe(0);
  });

  it('should open after failure threshold', async () => {
    const breaker = new CircuitBreaker(3, 1000);

    // Fail 3 times
    for (let i = 0; i < 3; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    expect(breaker.getState()).toBe(CircuitState.OPEN);
    expect(breaker.getFailureCount()).toBe(3);
  });

  it('should reject calls when open', async () => {
    const breaker = new CircuitBreaker(2, 1000);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    // Next call should be rejected
    await expect(
      breaker.call(async () => 'success'),
    ).rejects.toThrow('is OPEN');
  });

  it('should enter HALF_OPEN after timeout', async () => {
    const breaker = new CircuitBreaker(2, 100);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    expect(breaker.getState()).toBe(CircuitState.OPEN);

    // Wait for recovery timeout
    await new Promise((resolve) => setTimeout(resolve, 150));

    // Next call should transition to HALF_OPEN
    await breaker.call(async () => 'success');
  });

  it('should close after successful recovery', async () => {
    const breaker = new CircuitBreaker(2, 100);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    // Wait for recovery timeout
    await new Promise((resolve) => setTimeout(resolve, 150));

    // Two successful calls should close the circuit
    await breaker.call(async () => 'success');
    await breaker.call(async () => 'success');

    expect(breaker.getState()).toBe(CircuitState.CLOSED);
    expect(breaker.getFailureCount()).toBe(0);
  });

  it('should reopen on HALF_OPEN failure', async () => {
    const breaker = new CircuitBreaker(2, 100);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    // Wait for recovery timeout
    await new Promise((resolve) => setTimeout(resolve, 150));

    // Fail during HALF_OPEN
    try {
      await breaker.call(async () => {
        throw new Error('fail');
      });
    } catch (e) {
      // Expected
    }

    expect(breaker.getState()).toBe(CircuitState.OPEN);
  });

  it('should reset failure count on success', async () => {
    const breaker = new CircuitBreaker(3);

    // Fail once
    try {
      await breaker.call(async () => {
        throw new Error('fail');
      });
    } catch (e) {
      // Expected
    }

    expect(breaker.getFailureCount()).toBe(1);

    // Succeed
    await breaker.call(async () => 'success');

    expect(breaker.getFailureCount()).toBe(0);
  });

  it('should support manual reset', async () => {
    const breaker = new CircuitBreaker(2);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.call(async () => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    expect(breaker.getState()).toBe(CircuitState.OPEN);

    // Manual reset
    breaker.reset();

    expect(breaker.getState()).toBe(CircuitState.CLOSED);
    expect(breaker.getFailureCount()).toBe(0);
  });

  it('should work with sync functions', () => {
    const breaker = new CircuitBreaker(2);

    // Open the circuit
    for (let i = 0; i < 2; i++) {
      try {
        breaker.callSync(() => {
          throw new Error('fail');
        });
      } catch (e) {
        // Expected
      }
    }

    expect(breaker.getState()).toBe(CircuitState.OPEN);

    // Should reject next call
    expect(() => breaker.callSync(() => 'success')).toThrow('is OPEN');
  });
});

describe('Graceful Degradation', () => {
  it('should use fallback on primary failure', async () => {
    const primary = async () => {
      throw new Error('primary failed');
    };
    const fallback = async () => 'fallback success';

    const result = await withFallback(primary, fallback);

    expect(result).toBe('fallback success');
  });

  it('should use primary when successful', async () => {
    const primary = async () => 'primary success';
    const fallback = async () => 'fallback success';

    const result = await withFallback(primary, fallback);

    expect(result).toBe('primary success');
  });

  it('should respect fallback condition', async () => {
    const primary = async () => {
      throw new Error('primary failed');
    };
    const fallback = async () => 'fallback success';

    // Only fallback on Error
    const result = await withFallback(
      primary,
      fallback,
      (error) => error instanceof Error,
    );

    expect(result).toBe('fallback success');
  });

  it('should not fallback when condition is false', async () => {
    const primary = async () => {
      throw new TypeError('type error');
    };
    const fallback = async () => 'fallback success';

    // Don't fallback on TypeError
    await expect(
      withFallback(primary, fallback, (error) => !(error instanceof TypeError)),
    ).rejects.toThrow('type error');
  });
});

describe('Timeout Wrapper', () => {
  it('should complete before timeout', async () => {
    const fn = async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      return 'success';
    };

    const result = await withTimeout(fn, 100);

    expect(result).toBe('success');
  });

  it('should timeout and throw', async () => {
    const fn = async () => {
      await new Promise((resolve) => setTimeout(resolve, 200));
      return 'success';
    };

    await expect(withTimeout(fn, 100)).rejects.toThrow('timed out');
  });

  it('should use custom timeout error', async () => {
    const fn = async () => {
      await new Promise((resolve) => setTimeout(resolve, 200));
      return 'success';
    };

    const customError = new Error('Custom timeout');

    await expect(withTimeout(fn, 100, customError)).rejects.toThrow(
      'Custom timeout',
    );
  });
});
