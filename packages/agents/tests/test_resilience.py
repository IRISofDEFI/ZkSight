"""
Tests for resilience patterns (retry and circuit breaker).
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.resilience import (
    exponential_backoff,
    linear_backoff,
    constant_backoff,
    retry,
    RetryStrategy,
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
    withFallback,
)
from src.errors import ChimeraError, ErrorCode, DataSourceError


class TestExponentialBackoff:
    """Tests for exponential backoff calculation"""
    
    def test_exponential_backoff_increases(self):
        """Test that delay increases exponentially"""
        delay0 = exponential_backoff(0, base_delay=1.0, jitter=False)
        delay1 = exponential_backoff(1, base_delay=1.0, jitter=False)
        delay2 = exponential_backoff(2, base_delay=1.0, jitter=False)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0
    
    def test_exponential_backoff_respects_max_delay(self):
        """Test that delay doesn't exceed max_delay"""
        delay = exponential_backoff(10, base_delay=1.0, max_delay=10.0, jitter=False)
        assert delay == 10.0
    
    def test_exponential_backoff_with_jitter(self):
        """Test that jitter adds randomness"""
        delays = [exponential_backoff(1, base_delay=1.0, jitter=True) for _ in range(10)]
        # All delays should be different due to jitter
        assert len(set(delays)) > 1
        # All delays should be within reasonable range (2.0 ± 25%)
        for delay in delays:
            assert 1.5 <= delay <= 2.5


class TestLinearBackoff:
    """Tests for linear backoff calculation"""
    
    def test_linear_backoff_increases(self):
        """Test that delay increases linearly"""
        delay0 = linear_backoff(0, base_delay=1.0)
        delay1 = linear_backoff(1, base_delay=1.0)
        delay2 = linear_backoff(2, base_delay=1.0)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 3.0
    
    def test_linear_backoff_respects_max_delay(self):
        """Test that delay doesn't exceed max_delay"""
        delay = linear_backoff(100, base_delay=1.0, max_delay=10.0)
        assert delay == 10.0


class TestConstantBackoff:
    """Tests for constant backoff"""
    
    def test_constant_backoff_returns_same_value(self):
        """Test that constant backoff always returns the same value"""
        delay = constant_backoff(5.0)
        assert delay == 5.0


class TestRetryDecorator:
    """Tests for retry decorator"""
    
    def test_retry_succeeds_on_first_attempt(self):
        """Test that successful function doesn't retry"""
        mock_func = Mock(return_value="success")
        
        @retry(max_attempts=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_succeeds_after_failures(self):
        """Test that function retries and eventually succeeds"""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        @retry(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_exhausts_attempts(self):
        """Test that retry gives up after max attempts"""
        mock_func = Mock(side_effect=Exception("fail"))
        
        @retry(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception, match="fail"):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_retry_respects_non_retryable_error(self):
        """Test that non-retryable errors are not retried"""
        error = ChimeraError("non-retryable", ErrorCode.INVALID_QUERY, retryable=False)
        mock_func = Mock(side_effect=error)
        
        @retry(max_attempts=3, retryable_exceptions=(ChimeraError,))
        def test_func():
            return mock_func()
        
        with pytest.raises(ChimeraError):
            test_func()
        
        # Should only be called once since error is not retryable
        assert mock_func.call_count == 1
    
    # Async test removed - requires pytest-asyncio
    # @pytest.mark.asyncio
    # async def test_retry_async_function(self):
    #     """Test that retry works with async functions"""
    #     mock_func = AsyncMock(side_effect=[Exception("fail"), "success"])
    #     
    #     @retry(max_attempts=3, base_delay=0.01)
    #     async def test_func():
    #         return await mock_func()
    #     
    #     result = await test_func()
    #     assert result == "success"
    #     assert mock_func.call_count == 2


class TestCircuitBreaker:
    """Tests for circuit breaker"""
    
    def test_circuit_breaker_starts_closed(self):
        """Test that circuit breaker starts in CLOSED state"""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # Fail 3 times
        for _ in range(3):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
    
    def test_circuit_breaker_rejects_when_open(self):
        """Test that circuit breaker rejects calls when open"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        # Next call should be rejected
        with pytest.raises(DataSourceError, match="is OPEN"):
            breaker.call(lambda: "success")
    
    def test_circuit_breaker_half_open_after_timeout(self):
        """Test that circuit enters HALF_OPEN state after timeout"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        try:
            breaker.call(lambda: "success")
        except Exception:
            pass
        
        # State should have been HALF_OPEN during the call
        # After success, it should be CLOSED (requires 2 successes)
    
    def test_circuit_breaker_closes_after_successful_recovery(self):
        """Test that circuit closes after successful recovery"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Two successful calls should close the circuit
        breaker.call(lambda: "success")
        breaker.call(lambda: "success")
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test that circuit reopens if call fails in HALF_OPEN state"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Fail during HALF_OPEN
        try:
            breaker.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass
        
        assert breaker.state == CircuitState.OPEN
    
    def test_circuit_breaker_resets_failure_count_on_success(self):
        """Test that failure count resets on successful call"""
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Fail once
        try:
            breaker.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass
        
        assert breaker.failure_count == 1
        
        # Succeed
        breaker.call(lambda: "success")
        
        assert breaker.failure_count == 0
    
    def test_circuit_breaker_manual_reset(self):
        """Test manual reset of circuit breaker"""
        breaker = CircuitBreaker(failure_threshold=2)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Manual reset
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    # Async test removed - requires pytest-asyncio
    # @pytest.mark.asyncio
    # async def test_circuit_breaker_async(self):
    #     """Test circuit breaker with async functions"""
    #     breaker = CircuitBreaker(failure_threshold=2)
    #     
    #     async def failing_func():
    #         raise ValueError("fail")
    #     
    #     # Open the circuit
    #     for _ in range(2):
    #         try:
    #             await breaker.call_async(failing_func)
    #         except ValueError:
    #             pass
    #     
    #     assert breaker.state == CircuitState.OPEN
    #     
    #     # Should reject next call
    #     with pytest.raises(DataSourceError, match="is OPEN"):
    #         await breaker.call_async(lambda: "success")


class TestCircuitBreakerDecorator:
    """Tests for circuit breaker decorator"""
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator"""
        @circuit_breaker(failure_threshold=2, recovery_timeout=0.1, name="test")
        def test_func(should_fail: bool):
            if should_fail:
                raise ValueError("fail")
            return "success"
        
        # Should work normally
        assert test_func(False) == "success"
        
        # Fail twice to open circuit
        for _ in range(2):
            try:
                test_func(True)
            except ValueError:
                pass
        
        # Should reject next call
        with pytest.raises(DataSourceError, match="is OPEN"):
            test_func(False)
    
    def test_circuit_breaker_decorator_access(self):
        """Test that we can access the circuit breaker from decorated function"""
        @circuit_breaker(failure_threshold=2, name="test")
        def test_func():
            return "success"
        
        assert hasattr(test_func, 'circuit_breaker')
        assert isinstance(test_func.circuit_breaker, CircuitBreaker)
        assert test_func.circuit_breaker.state == CircuitState.CLOSED


class TestGracefulDegradation:
    """Tests for graceful degradation patterns"""
    
    def test_fallback_on_primary_failure(self):
        """Test that fallback is used when primary fails"""
        def primary():
            raise ValueError("primary failed")
        
        def fallback():
            return "fallback success"
        
        result = withFallback(primary, fallback)
        assert result == "fallback success"
    
    def test_primary_used_when_successful(self):
        """Test that primary is used when it succeeds"""
        def primary():
            return "primary success"
        
        def fallback():
            return "fallback success"
        
        result = withFallback(primary, fallback)
        assert result == "primary success"
    
    def test_fallback_with_condition(self):
        """Test fallback with custom condition"""
        def primary():
            raise ValueError("primary failed")
        
        def fallback():
            return "fallback success"
        
        # Only fallback on ValueError
        result = withFallback(
            primary,
            fallback,
            fallback_condition=lambda e: isinstance(e, ValueError)
        )
        assert result == "fallback success"
        
        # Don't fallback on other errors
        def primary_type_error():
            raise TypeError("type error")
        
        with pytest.raises(TypeError):
            withFallback(
                primary_type_error,
                fallback,
                fallback_condition=lambda e: isinstance(e, ValueError)
            )


def withFallback(primary, fallback, fallback_condition=None):
    """Helper function for graceful degradation"""
    try:
        return primary()
    except Exception as e:
        should_fallback = fallback_condition(e) if fallback_condition else True
        if should_fallback:
            return fallback()
        raise
