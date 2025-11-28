/**
 * Authentication and authorization middleware
 */
import { Request, Response, NextFunction } from 'express';
import { JwtService } from './jwt';
import { AuthDatabase } from './database';
import { UserRole } from './types';
import { ApiError } from '../middleware/errorHandler';

export class AuthMiddleware {
  private jwtService: JwtService;
  private authDb: AuthDatabase;

  constructor(jwtService: JwtService, authDb: AuthDatabase) {
    this.jwtService = jwtService;
    this.authDb = authDb;
  }

  /**
   * Authenticate request using JWT or API key
   */
  authenticate = async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      // Check for JWT token in Authorization header
      const authHeader = req.headers.authorization;
      if (authHeader && authHeader.startsWith('Bearer ')) {
        const token = authHeader.substring(7);
        const payload = this.jwtService.verifyToken(token);
        
        // Load user from database
        const user = await this.authDb.findUserById(payload.userId);
        if (!user) {
          throw this.createAuthError('User not found');
        }
        
        req.user = user;
        return next();
      }

      // Check for API key in header
      const apiKey = req.headers['x-api-key'] as string;
      if (apiKey) {
        const key = await this.authDb.verifyApiKey(apiKey);
        if (!key) {
          throw this.createAuthError('Invalid API key');
        }
        
        req.apiKey = key;
        return next();
      }

      // No authentication provided
      throw this.createAuthError('Authentication required');
    } catch (error) {
      next(error);
    }
  };

  /**
   * Optional authentication (doesn't fail if not authenticated)
   */
  optionalAuth = async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      await this.authenticate(req, res, () => {});
    } catch (error) {
      // Ignore authentication errors
    }
    next();
  };

  /**
   * Require specific role(s)
   */
  requireRole = (...roles: UserRole[]) => {
    return (req: Request, res: Response, next: NextFunction): void => {
      if (!req.user) {
        return next(this.createAuthError('Authentication required'));
      }

      if (!roles.includes(req.user.role)) {
        return next(this.createForbiddenError('Insufficient permissions'));
      }

      next();
    };
  };

  /**
   * Require specific scope(s) for API key
   */
  requireScope = (...scopes: string[]) => {
    return (req: Request, res: Response, next: NextFunction): void => {
      if (!req.apiKey) {
        return next(this.createAuthError('API key required'));
      }

      const hasAllScopes = scopes.every((scope) =>
        req.apiKey!.scopes.includes(scope)
      );

      if (!hasAllScopes) {
        return next(this.createForbiddenError('Insufficient API key scopes'));
      }

      next();
    };
  };

  /**
   * Create authentication error
   */
  private createAuthError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 401;
    error.code = 'UNAUTHORIZED';
    error.retryable = false;
    return error;
  }

  /**
   * Create forbidden error
   */
  private createForbiddenError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 403;
    error.code = 'FORBIDDEN';
    error.retryable = false;
    return error;
  }
}
