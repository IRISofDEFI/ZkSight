/**
 * Middleware to add correlation IDs to requests for distributed tracing
 */
import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

declare global {
  namespace Express {
    interface Request {
      correlationId: string;
    }
  }
}

export function correlationIdMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Use existing correlation ID from header or generate new one
  const correlationId = (req.headers['x-correlation-id'] as string) || uuidv4();
  
  req.correlationId = correlationId;
  res.setHeader('X-Correlation-ID', correlationId);
  
  next();
}
