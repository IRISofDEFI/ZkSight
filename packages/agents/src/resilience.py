"""
Resilience patterns for Chimera agents.

This module provides retry logic with exponential backoff and circuit breaker
patterns for handling failures in external service calls.
"""
import time
import asyncio
from typing import Callable, TypeVar, Optional, Any, Dict
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
import logging

from .errors import ChimeraError, ErrorCode, DataSourceError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryStrategy(str, Enum):
    """Retry strategies"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
    
    Returns:
        Delay in seconds
    """
    import random
    
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_amount = delay * 0.25
        delay = delay + random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)


def linear_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> float:
    """
    Calculate linear backoff delay.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Delay in seconds
    """
    return min(base_delay * (attempt + 1), max_delay)


def constant_backoff(delay: float = 1.0) -> float:
    """
    Return constant delay.
    
    Args:
        delay: Delay in seconds
    
    Returns:
        Delay in seconds
    """
    return delay


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None,
    ):
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            return exponential_backoff(attempt, self.base_delay, self.max_delay, self.jitter)
        elif self.strategy == RetryStrategy.LINEAR:
            return linear_backoff(attempt, self.base_delay, self.max_delay)
        else:  # CONSTANT
            return constant_backoff(self.base_delay)


def retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[tuple] = None,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        retryable_exceptions: Tuple of exceptions to retry on
    
    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions,
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if error is retryable
                    if isinstance(e, ChimeraError) and not e.retryable:
                        raise
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed. Last error: {e}"
                        )
            
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if error is retryable
                    if isinstance(e, ChimeraError) and not e.retryable:
                        raise
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed. Last error: {e}"
                        )
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    The circuit breaker prevents cascading failures by stopping requests
    to a failing service and allowing it time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: Optional[str] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to count as failure
            name: Optional name for the circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "unnamed"
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._success_count = 0
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count"""
        return self._failure_count
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self._state != CircuitState.OPEN:
            return False
        
        if self._last_failure_time is None:
            return False
        
        time_since_failure = datetime.now() - self._last_failure_time
        return time_since_failure >= timedelta(seconds=self.recovery_timeout)
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call a function through the circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            DataSourceError: If circuit is open
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
        
        # Reject if circuit is open
        if self._state == CircuitState.OPEN:
            raise DataSourceError(
                f"Circuit breaker '{self.name}' is OPEN",
                source=self.name,
                code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
                retryable=True,
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call an async function through the circuit breaker.
        
        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            DataSourceError: If circuit is open
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
        
        # Reject if circuit is open
        if self._state == CircuitState.OPEN:
            raise DataSourceError(
                f"Circuit breaker '{self.name}' is OPEN",
                source=self.name,
                code=ErrorCode.DATA_SOURCE_UNAVAILABLE,
                retryable=True,
            )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            # Require 2 successes to close circuit
            if self._success_count >= 2:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' closed after recovery")
        else:
            # Reset failure count on success
            self._failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call"""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            # Failed during recovery, reopen circuit
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' reopened after failed recovery")
        elif self._failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            self._state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker '{self.name}' opened after {self._failure_count} failures"
            )
    
    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' manually reset")


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception,
    name: Optional[str] = None,
) -> Callable:
    """
    Decorator to wrap a function with a circuit breaker.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to count as failure
        name: Optional name for the circuit breaker
    
    Returns:
        Decorated function
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        name=name,
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await breaker.call_async(func, *args, **kwargs)
        
        # Attach breaker to function for manual control
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Get a circuit breaker by name"""
    return _circuit_breakers.get(name)


def register_circuit_breaker(name: str, breaker: CircuitBreaker) -> None:
    """Register a circuit breaker"""
    _circuit_breakers[name] = breaker


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers"""
    return _circuit_breakers.copy()


def withFallback(
    primary: Callable[[], T],
    fallback: Callable[[], T],
    fallback_condition: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """
    Execute primary function with fallback on failure (graceful degradation).
    
    Args:
        primary: Primary function to execute
        fallback: Fallback function to execute on failure
        fallback_condition: Optional condition to determine if fallback should be used
    
    Returns:
        Result from primary or fallback function
    """
    try:
        return primary()
    except Exception as e:
        should_fallback = fallback_condition(e) if fallback_condition else True
        if should_fallback:
            logger.warning(
                f"Primary operation failed, using fallback: {e}",
                extra={"error": str(e)}
            )
            return fallback()
        raise


async def withFallbackAsync(
    primary: Callable[[], T],
    fallback: Callable[[], T],
    fallback_condition: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """
    Execute async primary function with fallback on failure (graceful degradation).
    
    Args:
        primary: Primary async function to execute
        fallback: Fallback async function to execute on failure
        fallback_condition: Optional condition to determine if fallback should be used
    
    Returns:
        Result from primary or fallback function
    """
    try:
        return await primary()
    except Exception as e:
        should_fallback = fallback_condition(e) if fallback_condition else True
        if should_fallback:
            logger.warning(
                f"Primary operation failed, using fallback: {e}",
                extra={"error": str(e)}
            )
            return await fallback()
        raise


def withTimeout(
    func: Callable[[], T],
    timeout_seconds: float,
    timeout_error: Optional[Exception] = None,
) -> T:
    """
    Execute function with timeout (sync version).
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds
        timeout_error: Optional custom error to raise on timeout
    
    Returns:
        Function result
    
    Raises:
        TimeoutError or custom timeout error
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
    
    # Set the signal handler and alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout_seconds))
    
    try:
        result = func()
        signal.alarm(0)  # Disable the alarm
        return result
    except TimeoutError:
        if timeout_error:
            raise timeout_error
        raise


async def withTimeoutAsync(
    func: Callable[[], T],
    timeout_seconds: float,
    timeout_error: Optional[Exception] = None,
) -> T:
    """
    Execute async function with timeout.
    
    Args:
        func: Async function to execute
        timeout_seconds: Timeout in seconds
        timeout_error: Optional custom error to raise on timeout
    
    Returns:
        Function result
    
    Raises:
        asyncio.TimeoutError or custom timeout error
    """
    try:
        return await asyncio.wait_for(func(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        if timeout_error:
            raise timeout_error
        raise ChimeraError(
            f"Operation timed out after {timeout_seconds}s",
            ErrorCode.DATA_SOURCE_TIMEOUT,
            retryable=True,
        )
