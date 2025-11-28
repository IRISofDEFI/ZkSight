import { MongoClient, Db } from 'mongodb';
import { loadConfig } from '../config';
import { initializeCollections } from '../models';

let client: MongoClient | null = null;
let db: Db | null = null;

/**
 * Connect to MongoDB and initialize collections
 */
export async function connectMongoDB(): Promise<Db> {
  if (db) {
    return db;
  }

  const config = loadConfig();
  
  try {
    client = new MongoClient(config.mongodb.uri, {
      maxPoolSize: 10,
      minPoolSize: 2,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });

    await client.connect();
    console.log('Connected to MongoDB');

    db = client.db(config.mongodb.database);
    
    // Initialize collections and indexes
    await initializeCollections(db);
    
    return db;
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

/**
 * Get the MongoDB database instance
 */
export function getMongoDB(): Db {
  if (!db) {
    throw new Error('MongoDB not connected. Call connectMongoDB() first.');
  }
  return db;
}

/**
 * Close MongoDB connection
 */
export async function closeMongoDB(): Promise<void> {
  if (client) {
    await client.close();
    client = null;
    db = null;
    console.log('MongoDB connection closed');
  }
}

/**
 * Health check for MongoDB connection
 */
export async function checkMongoDBHealth(): Promise<boolean> {
  try {
    if (!db) {
      return false;
    }
    await db.admin().ping();
    return true;
  } catch (error) {
    console.error('MongoDB health check failed:', error);
    return false;
  }
}
