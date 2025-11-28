/**
 * JWT token generation and validation
 */
import jwt from 'jsonwebtoken';
import { Config } from '../config';
import { JwtPayload, User } from './types';

export class JwtService {
  private secret: string;
  private expiresIn: string;

  constructor(config: Config) {
    this.secret = config.auth.jwtSecret;
    this.expiresIn = config.auth.jwtExpiresIn;
  }

  /**
   * Generate JWT token for user
   */
  generateToken(user: User): string {
    const payload: JwtPayload = {
      userId: user.id,
      email: user.email,
      role: user.role,
    };

    return jwt.sign(payload, this.secret, {
      expiresIn: this.expiresIn,
      issuer: 'chimera-api',
      audience: 'chimera-client',
    });
  }

  /**
   * Verify and decode JWT token
   */
  verifyToken(token: string): JwtPayload {
    try {
      const decoded = jwt.verify(token, this.secret, {
        issuer: 'chimera-api',
        audience: 'chimera-client',
      }) as JwtPayload;

      return decoded;
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new Error('Token expired');
      } else if (error instanceof jwt.JsonWebTokenError) {
        throw new Error('Invalid token');
      }
      throw error;
    }
  }

  /**
   * Decode token without verification (for debugging)
   */
  decodeToken(token: string): JwtPayload | null {
    return jwt.decode(token) as JwtPayload | null;
  }
}
