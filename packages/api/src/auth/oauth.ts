/**
 * OAuth 2.0 / OpenID Connect integration
 */
import passport from 'passport';
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';
import { Strategy as GitHubStrategy } from 'passport-github2';
import { Config } from '../config';
import { AuthDatabase } from './database';
import { User, UserRole } from './types';

export class OAuthService {
  private authDb: AuthDatabase;
  private config: Config;

  constructor(config: Config, authDb: AuthDatabase) {
    this.config = config;
    this.authDb = authDb;
    this.setupStrategies();
  }

  /**
   * Setup OAuth strategies
   */
  private setupStrategies(): void {
    // Google OAuth
    if (
      this.config.auth.oauth?.google?.clientId &&
      this.config.auth.oauth?.google?.clientSecret
    ) {
      passport.use(
        new GoogleStrategy(
          {
            clientID: this.config.auth.oauth.google.clientId,
            clientSecret: this.config.auth.oauth.google.clientSecret,
            callbackURL: this.config.auth.oauth.google.callbackUrl || '/auth/google/callback',
          },
          async (accessToken, refreshToken, profile, done) => {
            try {
              const email = profile.emails?.[0]?.value;
              if (!email) {
                return done(new Error('No email found in profile'));
              }

              let user = await this.authDb.findUserByEmail(email);
              if (!user) {
                user = await this.authDb.createUser(email, UserRole.VIEWER);
              }

              return done(null, user);
            } catch (error) {
              return done(error as Error);
            }
          }
        )
      );
    }

    // GitHub OAuth
    if (
      this.config.auth.oauth?.github?.clientId &&
      this.config.auth.oauth?.github?.clientSecret
    ) {
      passport.use(
        new GitHubStrategy(
          {
            clientID: this.config.auth.oauth.github.clientId,
            clientSecret: this.config.auth.oauth.github.clientSecret,
            callbackURL: this.config.auth.oauth.github.callbackUrl || '/auth/github/callback',
          },
          async (accessToken: string, refreshToken: string, profile: any, done: any) => {
            try {
              const email = profile.emails?.[0]?.value;
              if (!email) {
                return done(new Error('No email found in profile'));
              }

              let user = await this.authDb.findUserByEmail(email);
              if (!user) {
                user = await this.authDb.createUser(email, UserRole.VIEWER);
              }

              return done(null, user);
            } catch (error) {
              return done(error as Error);
            }
          }
        )
      );
    }

    // Serialize/deserialize user
    passport.serializeUser((user: any, done) => {
      done(null, user.id);
    });

    passport.deserializeUser(async (id: string, done) => {
      try {
        const user = await this.authDb.findUserById(id);
        done(null, user);
      } catch (error) {
        done(error);
      }
    });
  }

  /**
   * Get passport instance
   */
  getPassport(): typeof passport {
    return passport;
  }
}
