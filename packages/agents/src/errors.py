"""
Error handling and standardization for Chimera agents.

This module provides a comprehensive error taxonomy and standardized error responses
for all agent operations.
"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for the Chimera system"""
    
    # Data Source Errors (2xx)
    DATA_SOURCE_UNAVAILABLE = "DATA_SOURCE_UNAVAILABLE"
    DATA_SOURCE_TIMEOUT = "DATA_SOURCE_TIMEOUT"
    DATA_SOURCE_RATE_LIMITED = "DATA_SOURCE_RATE_LIMITED"
    DATA_SOURCE_AUTH_FAILED = "DATA_SOURCE_AUTH_FAILED"
    DATA_SOURCE_INVALID_RESPONSE = "DATA_SOURCE_INVALID_RESPONSE"
    
    # Data Processing Errors (3xx)
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"
    
    # Analysis Errors (4xx)
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    CORRELATION_CALCULATION_FAILED = "CORRELATION_CALCULATION_FAILED"
    ANOMALY_DETECTION_FAILED = "ANOMALY_DETECTION_FAILED"
    PATTERN_RECOGNITION_FAILED = "PATTERN_RECOGNITION_FAILED"
    
    # Query Errors (5xx)
    INVALID_QUERY = "INVALID_QUERY"
    QUERY_PARSING_FAILED = "QUERY_PARSING_FAILED"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    UNSUPPORTED_QUERY_TYPE = "UNSUPPORTED_QUERY_TYPE"
    
    # LLM Errors (6xx)
    LLM_API_ERROR = "LLM_API_ERROR"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    
    # Verification Errors (7xx)
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    CLAIM_EXTRACTION_FAILED = "CLAIM_EXTRACTION_FAILED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    
    # System Errors (8xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    MESSAGE_BUS_ERROR = "MESSAGE_BUS_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # User Errors (9xx)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_INPUT = "INVALID_INPUT"


class ChimeraError(Exception):
    """Base exception class for all Chimera errors"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
        suggested_action: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.details = details or {}
        self.suggested_action = suggested_action
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for serialization"""
        result = {
            "code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.suggested_action:
            result["suggested_action"] = self.suggested_action
        
        return result


class DataSourceError(ChimeraError):
    """Errors related to external data sources"""
    
    def __init__(
        self,
        message: str,
        source: str,
        code: ErrorCode = ErrorCode.DATA_SOURCE_UNAVAILABLE,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["source"] = source
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Check data source connectivity and try again",
        )


class DataProcessingError(ChimeraError):
    """Errors related to data processing and validation"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_DATA_FORMAT,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Verify data format and schema",
        )


class AnalysisError(ChimeraError):
    """Errors related to data analysis operations"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.ANALYSIS_FAILED,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Check data quality and analysis parameters",
        )


class QueryError(ChimeraError):
    """Errors related to query processing"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_QUERY,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Rephrase your query or provide more context",
        )


class LLMError(ChimeraError):
    """Errors related to LLM API calls"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.LLM_API_ERROR,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Wait a moment and try again",
        )


class VerificationError(ChimeraError):
    """Errors related to fact checking and verification"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.VERIFICATION_FAILED,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Review the conflicting data sources",
        )


class SystemError(ChimeraError):
    """Errors related to system operations"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Contact system administrator if problem persists",
        )


class UserError(ChimeraError):
    """Errors related to user actions"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code=code,
            retryable=retryable,
            details=details,
            suggested_action="Check your input and try again",
        )


def create_error_response(
    error: ChimeraError,
    request_id: Optional[str] = None,
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        error: The ChimeraError instance
        request_id: Optional request/correlation ID
        timestamp: Optional timestamp (defaults to current time)
    
    Returns:
        Dictionary containing standardized error response
    """
    import time
    
    response = {
        "error": error.to_dict(),
    }
    
    if request_id:
        response["request_id"] = request_id
    
    response["timestamp"] = timestamp or int(time.time() * 1000)
    
    return response
