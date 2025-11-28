/**
 * Request logging middleware with structured logging
 */
import { Request, Response, NextFunction } from 'express';
import morgan from 'morgan';

// Custom token for correlation ID
morgan.token('correlation-id', (req: Request) => req.correlationId);

// Custom token for response time in ms
morgan.token('response-time-ms', (req: Request, res: Response) => {
  const responseTime = res.getHeader('X-Response-Time');
  return responseTime ? `${responseTime}ms` : '-';
});

// JSON format for structured logging
morgan.format('json', (tokens, req: Request, res: Response) => {
  return JSON.stringify({
    timestamp: new Date().toISOString(),
    correlationId: tokens['correlation-id'](req, res),
    method: tokens.method(req, res),
    url: tokens.url(req, res),
    status: tokens.status(req, res),
    responseTime: tokens['response-time'](req, res),
    contentLength: tokens.res(req, res, 'content-length'),
    userAgent: tokens['user-agent'](req, res),
    remoteAddr: tokens['remote-addr'](req, res),
  });
});

export const requestLogger = morgan('json', {
  skip: (req: Request) => req.path === '/health',
});
