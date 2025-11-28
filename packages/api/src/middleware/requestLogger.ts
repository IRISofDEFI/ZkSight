/**
 * Request logging middleware with structured logging
 */
import { Request, Response, NextFunction } from 'express';
import { logRequestStart, logRequestEnd, setCorrelationId } from '../logging';

/**
 * Middleware to log HTTP requests with structured logging
 */
export function requestLogger(req: Request, res: Response, next: NextFunction): void {
  const startTime = Date.now();
  const correlationId = req.correlationId || 'unknown';
  
  // Set correlation ID in async context
  setCorrelationId(correlationId);
  
  // Log request start
  logRequestStart(req.method, req.path, correlationId);
  
  // Capture response finish event
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    logRequestEnd(req.method, req.path, res.statusCode, duration, correlationId);
  });
  
  next();
}
