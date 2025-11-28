import { z } from 'zod';
import dotenv from 'dotenv';

dotenv.config();

const configSchema = z.object({
  environment: z.enum(['development', 'staging', 'production']).default('development'),
  port: z.coerce.number().min(1).max(65535).default(3000),
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  
  rabbitmq: z.object({
    host: z.string().default('localhost'),
    port: z.coerce.number().min(1).max(65535).default(5672),
    username: z.string().default('guest'),
    password: z.string().default('guest'),
    vhost: z.string().default('/'),
  }),
  
  mongodb: z.object({
    uri: z.string().default('mongodb://localhost:27017'),
    database: z.string().default('chimera'),
  }),
  
  redis: z.object({
    host: z.string().default('localhost'),
    port: z.coerce.number().min(1).max(65535).default(6379),
    password: z.string().optional(),
    db: z.coerce.number().min(0).max(15).default(0),
  }),
  
  cors: z.object({
    origin: z.string().default('*'),
    credentials: z.boolean().default(true),
  }),
  
  rateLimit: z.object({
    windowMs: z.coerce.number().default(60000),
    maxRequests: z.coerce.number().default(100),
  }),
  
  auth: z.object({
    jwtSecret: z.string().default('change-me-in-production'),
    jwtExpiresIn: z.string().default('24h'),
    oauth: z.object({
      google: z.object({
        clientId: z.string().optional(),
        clientSecret: z.string().optional(),
        callbackUrl: z.string().optional(),
      }).optional(),
      github: z.object({
        clientId: z.string().optional(),
        clientSecret: z.string().optional(),
        callbackUrl: z.string().optional(),
      }).optional(),
    }).optional(),
  }),
});

export type Config = z.infer<typeof configSchema>;

export function loadConfig(): Config {
  const rawConfig = {
    environment: process.env.NODE_ENV,
    port: process.env.PORT,
    logLevel: process.env.LOG_LEVEL,
    
    rabbitmq: {
      host: process.env.RABBITMQ_HOST,
      port: process.env.RABBITMQ_PORT,
      username: process.env.RABBITMQ_USERNAME,
      password: process.env.RABBITMQ_PASSWORD,
      vhost: process.env.RABBITMQ_VHOST,
    },
    
    mongodb: {
      uri: process.env.MONGODB_URI,
      database: process.env.MONGODB_DATABASE,
    },
    
    redis: {
      host: process.env.REDIS_HOST,
      port: process.env.REDIS_PORT,
      password: process.env.REDIS_PASSWORD,
      db: process.env.REDIS_DB,
    },
    
    cors: {
      origin: process.env.CORS_ORIGIN,
      credentials: process.env.CORS_CREDENTIALS === 'true',
    },
    
    rateLimit: {
      windowMs: process.env.RATE_LIMIT_WINDOW_MS,
      maxRequests: process.env.RATE_LIMIT_MAX_REQUESTS,
    },
    
    auth: {
      jwtSecret: process.env.JWT_SECRET,
      jwtExpiresIn: process.env.JWT_EXPIRES_IN,
      oauth: {
        google: {
          clientId: process.env.GOOGLE_CLIENT_ID,
          clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          callbackUrl: process.env.GOOGLE_CALLBACK_URL,
        },
        github: {
          clientId: process.env.GITHUB_CLIENT_ID,
          clientSecret: process.env.GITHUB_CLIENT_SECRET,
          callbackUrl: process.env.GITHUB_CALLBACK_URL,
        },
      },
    },
  };
  
  return configSchema.parse(rawConfig);
}
