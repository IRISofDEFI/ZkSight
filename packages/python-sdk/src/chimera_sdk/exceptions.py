"""Exceptions for Chimera SDK."""

from typing import Optional, Dict, Any
from .types import ErrorResponse


class ChimeraError(Exception):
    """Base exception for Chimera SDK errors."""

    def __init__(
        self,
        error_response: Optional[ErrorResponse] = None,
        message: Optional[str] = None,
        code: Optional[str] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[int] = None,
    ) -> None:
        """Initialize the error.

        Args:
            error_response: Error response from API
            message: Error message
            code: Error code
            retryable: Whether the error is retryable
            details: Additional error details
            request_id: Request ID
            timestamp: Error timestamp
        """
        if error_response:
            self.code = error_response.error.code
            self.message = error_response.error.message
            self.retryable = error_response.error.retryable
            self.details = error_response.error.details
            self.request_id = error_response.request_id
            self.timestamp = error_response.timestamp
        else:
            self.code = code or "UNKNOWN_ERROR"
            self.message = message or "An unknown error occurred"
            self.retryable = retryable
            self.details = details
            self.request_id = request_id
            self.timestamp = timestamp

        super().__init__(self.message)

    @classmethod
    def from_http_error(cls, error: Exception) -> "ChimeraError":
        """Create ChimeraError from HTTP error.

        Args:
            error: HTTP error

        Returns:
            ChimeraError instance
        """
        return cls(
            message=f"HTTP error: {str(error)}",
            code="HTTP_ERROR",
            retryable=False,
        )

    @classmethod
    def from_request_error(cls, error: Exception) -> "ChimeraError":
        """Create ChimeraError from request error.

        Args:
            error: Request error

        Returns:
            ChimeraError instance
        """
        return cls(
            message=f"Request error: {str(error)}",
            code="REQUEST_ERROR",
            retryable=True,
        )


class RateLimitError(ChimeraError):
    """Rate limit exceeded error."""

    def __init__(self, error_response: ErrorResponse) -> None:
        """Initialize the error.

        Args:
            error_response: Error response from API
        """
        super().__init__(error_response)


class AuthenticationError(ChimeraError):
    """Authentication error."""

    def __init__(self, error_response: ErrorResponse) -> None:
        """Initialize the error.

        Args:
            error_response: Error response from API
        """
        super().__init__(error_response)


class NotFoundError(ChimeraError):
    """Resource not found error."""

    def __init__(self, error_response: ErrorResponse) -> None:
        """Initialize the error.

        Args:
            error_response: Error response from API
        """
        super().__init__(error_response)


class ValidationError(ChimeraError):
    """Validation error."""

    def __init__(self, error_response: ErrorResponse) -> None:
        """Initialize the error.

        Args:
            error_response: Error response from API
        """
        super().__init__(error_response)
