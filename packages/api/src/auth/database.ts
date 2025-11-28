/**
 * Database operations for authentication
 */
import { MongoClient, Db, Collection } from 'mongodb';
import bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { User, ApiKey, UserRole } from './types';
import { Config } from '../config';

export class AuthDatabase {
  private client: MongoClient;
  private db!: Db;
  private users!: Collection<User>;
  private apiKeys!: Collection<ApiKey>;

  constructor(config: Config) {
    this.client = new MongoClient(config.mongodb.uri);
  }

  /**
   * Connect to database
   */
  async connect(dbName: string): Promise<void> {
    await this.client.connect();
    this.db = this.client.db(dbName);
    this.users = this.db.collection<User>('users');
    this.apiKeys = this.db.collection<ApiKey>('api_keys');

    // Create indexes
    await this.users.createIndex({ email: 1 }, { unique: true });
    await this.apiKeys.createIndex({ key: 1 }, { unique: true });
    await this.apiKeys.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 });
  }

  /**
   * Find user by email
   */
  async findUserByEmail(email: string): Promise<User | null> {
    return this.users.findOne({ email });
  }

  /**
   * Find user by ID
   */
  async findUserById(id: string): Promise<User | null> {
    return this.users.findOne({ id });
  }

  /**
   * Create new user
   */
  async createUser(email: string, role: UserRole = UserRole.VIEWER): Promise<User> {
    const user: User = {
      id: uuidv4(),
      email,
      role,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    await this.users.insertOne(user);
    return user;
  }

  /**
   * Update user
   */
  async updateUser(id: string, updates: Partial<User>): Promise<User | null> {
    const result = await this.users.findOneAndUpdate(
      { id },
      { $set: { ...updates, updatedAt: new Date() } },
      { returnDocument: 'after' }
    );

    return result || null;
  }

  /**
   * Create API key for user
   */
  async createApiKey(
    userId: string,
    name: string,
    scopes: string[],
    expiresAt?: Date
  ): Promise<{ apiKey: ApiKey; rawKey: string }> {
    const rawKey = `ck_${uuidv4().replace(/-/g, '')}`;
    const hashedKey = await bcrypt.hash(rawKey, 10);

    const apiKey: ApiKey = {
      id: uuidv4(),
      key: hashedKey,
      name,
      scopes,
      createdAt: new Date(),
      expiresAt,
    };

    await this.apiKeys.insertOne(apiKey);

    // Add API key reference to user
    await this.users.updateOne(
      { id: userId },
      { $push: { apiKeys: { id: apiKey.id, name: apiKey.name } } as any }
    );

    return { apiKey, rawKey };
  }

  /**
   * Verify API key
   */
  async verifyApiKey(rawKey: string): Promise<ApiKey | null> {
    const allKeys = await this.apiKeys.find({}).toArray();

    for (const key of allKeys) {
      const isValid = await bcrypt.compare(rawKey, key.key);
      if (isValid) {
        // Check if expired
        if (key.expiresAt && key.expiresAt < new Date()) {
          return null;
        }

        // Update last used timestamp
        await this.apiKeys.updateOne(
          { id: key.id },
          { $set: { lastUsedAt: new Date() } }
        );

        return key;
      }
    }

    return null;
  }

  /**
   * Revoke API key
   */
  async revokeApiKey(keyId: string): Promise<boolean> {
    const result = await this.apiKeys.deleteOne({ id: keyId });
    return result.deletedCount > 0;
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    await this.client.close();
  }
}
