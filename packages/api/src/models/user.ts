import { ObjectId } from 'mongodb';

/**
 * User profile schema
 * Requirements: 8.1, 8.3, 10.1, 11.1
 */

export type ExpertiseLevel = 'beginner' | 'intermediate' | 'expert';

export interface NotificationSettings {
  email: boolean;
  webhook: boolean;
  inApp: boolean;
  sms: boolean;
}

export interface UserPreferences {
  defaultTimeRange: {
    start: string;
    end: string;
  };
  favoriteMetrics: string[];
  notificationSettings: NotificationSettings;
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
  scopes: string[];
  createdAt: Date;
  lastUsedAt?: Date;
  expiresAt?: Date;
}

export interface UserProfile {
  _id?: ObjectId;
  userId: string;
  email: string;
  passwordHash?: string;
  expertiseLevel: ExpertiseLevel;
  preferences: UserPreferences;
  dashboardIds: string[];
  apiKeys: ApiKey[];
  createdAt: Date;
  updatedAt: Date;
}

export const USER_COLLECTION = 'users';

/**
 * MongoDB indexes for user collection
 */
export const USER_INDEXES = [
  {
    key: { userId: 1 },
    unique: true,
    name: 'idx_userId',
  },
  {
    key: { email: 1 },
    unique: true,
    name: 'idx_email',
  },
  {
    key: { 'apiKeys.key': 1 },
    sparse: true,
    name: 'idx_apiKey',
  },
  {
    key: { createdAt: 1 },
    name: 'idx_createdAt',
  },
];
