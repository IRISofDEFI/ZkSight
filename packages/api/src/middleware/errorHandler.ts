/**
 * Global error handling middleware
 */
import { Request, Response, NextFunction } from 'express';
import { ChimeraError, ErrorCode, createErrorResponse, UserError } from '../errors';
import { logError } from '../logging';

export function errorHandler(
  err: Error | ChimeraError,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Convert to ChimeraError if it's a standard Error
  const chimeraError = err instanceof ChimeraError
    ? err
    : new ChimeraError(
        err.message || 'An unexpected error occurred',
        ErrorCode.INTERNAL_SERVER_ERROR,
        false,
        { originalError: err.name }
      );

  // Log error with structured logging
  logError(chimeraError, {
    correlation_id: req.correlationId,
    method: req.method,
    path: req.path,
    code: chimeraError.code,
    retryable: chimeraError.retryable,
  });

  // Create standardized error response
  const errorResponse = createErrorResponse(
    chimeraError,
    req.correlationId,
    Date.now()
  );

  // Send error response
  res.status(chimeraError.statusCode).json(errorResponse);
}

export function notFoundHandler(req: Request, res: Response): void {
  const error = new UserError(
    `Route ${req.method} ${req.path} not found`,
    ErrorCode.NOT_FOUND,
    false
  );

  const errorResponse = createErrorResponse(
    error,
    req.correlationId,
    Date.now()
  );

  res.status(error.statusCode).json(errorResponse);
}
