/**
 * Rate limiting middleware
 */
import rateLimit from 'express-rate-limit';
import { Request, Response } from 'express';
import { Config } from '../config';

export function createRateLimiter(config: Config) {
  return rateLimit({
    windowMs: config.rateLimit.windowMs,
    max: config.rateLimit.maxRequests,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests, please try again later',
        retryAfter: Math.ceil(config.rateLimit.windowMs / 1000),
      },
    },
    keyGenerator: (req: Request) => {
      // Use API key if present, otherwise use IP
      return (req.headers['x-api-key'] as string) || req.ip || 'unknown';
    },
    handler: (req: Request, res: Response) => {
      res.status(429).json({
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests, please try again later',
          retryable: true,
          retryAfter: Math.ceil(config.rateLimit.windowMs / 1000),
        },
        requestId: req.correlationId,
        timestamp: Date.now(),
      });
    },
  });
}
