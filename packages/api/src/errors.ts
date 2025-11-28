/**
 * Error handling and standardization for Chimera API.
 * 
 * This module provides a comprehensive error taxonomy and standardized error responses
 * for all API operations.
 */

/**
 * Standardized error codes for the Chimera system
 */
export enum ErrorCode {
  // Data Source Errors (2xx)
  DATA_SOURCE_UNAVAILABLE = 'DATA_SOURCE_UNAVAILABLE',
  DATA_SOURCE_TIMEOUT = 'DATA_SOURCE_TIMEOUT',
  DATA_SOURCE_RATE_LIMITED = 'DATA_SOURCE_RATE_LIMITED',
  DATA_SOURCE_AUTH_FAILED = 'DATA_SOURCE_AUTH_FAILED',
  DATA_SOURCE_INVALID_RESPONSE = 'DATA_SOURCE_INVALID_RESPONSE',
  
  // Data Processing Errors (3xx)
  INSUFFICIENT_DATA = 'INSUFFICIENT_DATA',
  INVALID_DATA_FORMAT = 'INVALID_DATA_FORMAT',
  DATA_VALIDATION_FAILED = 'DATA_VALIDATION_FAILED',
  
  // Analysis Errors (4xx)
  ANALYSIS_FAILED = 'ANALYSIS_FAILED',
  CORRELATION_CALCULATION_FAILED = 'CORRELATION_CALCULATION_FAILED',
  ANOMALY_DETECTION_FAILED = 'ANOMALY_DETECTION_FAILED',
  PATTERN_RECOGNITION_FAILED = 'PATTERN_RECOGNITION_FAILED',
  
  // Query Errors (5xx)
  INVALID_QUERY = 'INVALID_QUERY',
  QUERY_PARSING_FAILED = 'QUERY_PARSING_FAILED',
  AMBIGUOUS_QUERY = 'AMBIGUOUS_QUERY',
  UNSUPPORTED_QUERY_TYPE = 'UNSUPPORTED_QUERY_TYPE',
  
  // LLM Errors (6xx)
  LLM_API_ERROR = 'LLM_API_ERROR',
  LLM_RATE_LIMITED = 'LLM_RATE_LIMITED',
  LLM_TIMEOUT = 'LLM_TIMEOUT',
  LLM_INVALID_RESPONSE = 'LLM_INVALID_RESPONSE',
  
  // Verification Errors (7xx)
  VERIFICATION_FAILED = 'VERIFICATION_FAILED',
  CLAIM_EXTRACTION_FAILED = 'CLAIM_EXTRACTION_FAILED',
  CONFLICT_DETECTED = 'CONFLICT_DETECTED',
  
  // System Errors (8xx)
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  CACHE_ERROR = 'CACHE_ERROR',
  MESSAGE_BUS_ERROR = 'MESSAGE_BUS_ERROR',
  CONFIGURATION_ERROR = 'CONFIGURATION_ERROR',
  
  // User Errors (9xx)
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  INVALID_INPUT = 'INVALID_INPUT',
  NOT_FOUND = 'NOT_FOUND',
}

/**
 * HTTP status code mapping for error codes
 */
const ERROR_STATUS_MAP: Record<ErrorCode, number> = {
  // Data Source Errors
  [ErrorCode.DATA_SOURCE_UNAVAILABLE]: 503,
  [ErrorCode.DATA_SOURCE_TIMEOUT]: 504,
  [ErrorCode.DATA_SOURCE_RATE_LIMITED]: 429,
  [ErrorCode.DATA_SOURCE_AUTH_FAILED]: 502,
  [ErrorCode.DATA_SOURCE_INVALID_RESPONSE]: 502,
  
  // Data Processing Errors
  [ErrorCode.INSUFFICIENT_DATA]: 422,
  [ErrorCode.INVALID_DATA_FORMAT]: 422,
  [ErrorCode.DATA_VALIDATION_FAILED]: 422,
  
  // Analysis Errors
  [ErrorCode.ANALYSIS_FAILED]: 500,
  [ErrorCode.CORRELATION_CALCULATION_FAILED]: 500,
  [ErrorCode.ANOMALY_DETECTION_FAILED]: 500,
  [ErrorCode.PATTERN_RECOGNITION_FAILED]: 500,
  
  // Query Errors
  [ErrorCode.INVALID_QUERY]: 400,
  [ErrorCode.QUERY_PARSING_FAILED]: 400,
  [ErrorCode.AMBIGUOUS_QUERY]: 400,
  [ErrorCode.UNSUPPORTED_QUERY_TYPE]: 400,
  
  // LLM Errors
  [ErrorCode.LLM_API_ERROR]: 502,
  [ErrorCode.LLM_RATE_LIMITED]: 429,
  [ErrorCode.LLM_TIMEOUT]: 504,
  [ErrorCode.LLM_INVALID_RESPONSE]: 502,
  
  // Verification Errors
  [ErrorCode.VERIFICATION_FAILED]: 422,
  [ErrorCode.CLAIM_EXTRACTION_FAILED]: 500,
  [ErrorCode.CONFLICT_DETECTED]: 409,
  
  // System Errors
  [ErrorCode.INTERNAL_SERVER_ERROR]: 500,
  [ErrorCode.DATABASE_ERROR]: 500,
  [ErrorCode.CACHE_ERROR]: 500,
  [ErrorCode.MESSAGE_BUS_ERROR]: 500,
  [ErrorCode.CONFIGURATION_ERROR]: 500,
  
  // User Errors
  [ErrorCode.UNAUTHORIZED]: 401,
  [ErrorCode.FORBIDDEN]: 403,
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 429,
  [ErrorCode.QUOTA_EXCEEDED]: 429,
  [ErrorCode.INVALID_INPUT]: 400,
  [ErrorCode.NOT_FOUND]: 404,
};

/**
 * Base error class for all Chimera errors
 */
export class ChimeraError extends Error {
  public readonly code: ErrorCode;
  public readonly retryable: boolean;
  public readonly details?: Record<string, any>;
  public readonly suggestedAction?: string;
  public readonly statusCode: number;

  constructor(
    message: string,
    code: ErrorCode,
    retryable: boolean = false,
    details?: Record<string, any>,
    suggestedAction?: string,
  ) {
    super(message);
    this.name = 'ChimeraError';
    this.code = code;
    this.retryable = retryable;
    this.details = details;
    this.suggestedAction = suggestedAction;
    this.statusCode = ERROR_STATUS_MAP[code] || 500;
    
    // Maintains proper stack trace for where our error was thrown
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON(): Record<string, any> {
    const result: Record<string, any> = {
      code: this.code,
      message: this.message,
      retryable: this.retryable,
    };

    if (this.details) {
      result.details = this.details;
    }

    if (this.suggestedAction) {
      result.suggested_action = this.suggestedAction;
    }

    return result;
  }
}

/**
 * Errors related to external data sources
 */
export class DataSourceError extends ChimeraError {
  constructor(
    message: string,
    source: string,
    code: ErrorCode = ErrorCode.DATA_SOURCE_UNAVAILABLE,
    retryable: boolean = true,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      { ...details, source },
      'Check data source connectivity and try again',
    );
    this.name = 'DataSourceError';
  }
}

/**
 * Errors related to data processing and validation
 */
export class DataProcessingError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.INVALID_DATA_FORMAT,
    retryable: boolean = false,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Verify data format and schema',
    );
    this.name = 'DataProcessingError';
  }
}

/**
 * Errors related to data analysis operations
 */
export class AnalysisError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.ANALYSIS_FAILED,
    retryable: boolean = false,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Check data quality and analysis parameters',
    );
    this.name = 'AnalysisError';
  }
}

/**
 * Errors related to query processing
 */
export class QueryError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.INVALID_QUERY,
    retryable: boolean = false,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Rephrase your query or provide more context',
    );
    this.name = 'QueryError';
  }
}

/**
 * Errors related to LLM API calls
 */
export class LLMError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.LLM_API_ERROR,
    retryable: boolean = true,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Wait a moment and try again',
    );
    this.name = 'LLMError';
  }
}

/**
 * Errors related to fact checking and verification
 */
export class VerificationError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.VERIFICATION_FAILED,
    retryable: boolean = false,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Review the conflicting data sources',
    );
    this.name = 'VerificationError';
  }
}

/**
 * Errors related to system operations
 */
export class SystemError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    retryable: boolean = true,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Contact system administrator if problem persists',
    );
    this.name = 'SystemError';
  }
}

/**
 * Errors related to user actions
 */
export class UserError extends ChimeraError {
  constructor(
    message: string,
    code: ErrorCode = ErrorCode.INVALID_INPUT,
    retryable: boolean = false,
    details?: Record<string, any>,
  ) {
    super(
      message,
      code,
      retryable,
      details,
      'Check your input and try again',
    );
    this.name = 'UserError';
  }
}

/**
 * Create a standardized error response
 */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    details?: Record<string, any>;
    suggested_action?: string;
  };
  request_id?: string;
  timestamp: number;
}

export function createErrorResponse(
  error: ChimeraError,
  requestId?: string,
  timestamp?: number,
): ErrorResponse {
  return {
    error: error.toJSON(),
    request_id: requestId,
    timestamp: timestamp || Date.now(),
  };
}
