/**
 * Global error handling middleware
 */
import { Request, Response, NextFunction } from 'express';

export interface ApiError extends Error {
  statusCode?: number;
  code?: string;
  retryable?: boolean;
  details?: Record<string, any>;
}

export function errorHandler(
  err: ApiError,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Log error
  console.error('Error:', {
    correlationId: req.correlationId,
    error: err.message,
    stack: err.stack,
    code: err.code,
  });

  // Determine status code
  const statusCode = err.statusCode || 500;
  
  // Determine error code
  const errorCode = err.code || 'INTERNAL_SERVER_ERROR';
  
  // Send error response
  res.status(statusCode).json({
    error: {
      code: errorCode,
      message: err.message || 'An unexpected error occurred',
      retryable: err.retryable ?? false,
      details: err.details,
    },
    requestId: req.correlationId,
    timestamp: Date.now(),
  });
}

export function notFoundHandler(req: Request, res: Response): void {
  res.status(404).json({
    error: {
      code: 'NOT_FOUND',
      message: `Route ${req.method} ${req.path} not found`,
      retryable: false,
    },
    requestId: req.correlationId,
    timestamp: Date.now(),
  });
}
