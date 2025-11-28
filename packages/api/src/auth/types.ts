/**
 * Authentication and authorization types
 */

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  VIEWER = 'viewer',
  DEVELOPER = 'developer',
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  apiKeys?: ApiKey[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ApiKey {
  id: string;
  key: string;
  name: string;
  scopes: string[];
  createdAt: Date;
  expiresAt?: Date;
  lastUsedAt?: Date;
}

export interface JwtPayload {
  userId: string;
  email: string;
  role: UserRole;
  iat?: number;
  exp?: number;
}

export interface AuthRequest extends Express.Request {
  user?: User;
  apiKey?: ApiKey;
}

declare global {
  namespace Express {
    interface Request {
      user?: User;
      apiKey?: ApiKey;
    }
  }
}
