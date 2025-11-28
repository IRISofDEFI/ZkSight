/**
 * MongoDB models and schemas
 * Requirements: 8.1, 8.3, 10.1, 11.1
 */

export * from './user';
export * from './dashboard';
export * from './report';
export * from './alert';
export * from './query';

import { Db, Collection } from 'mongodb';
import {
  USER_COLLECTION,
  USER_INDEXES,
  UserProfile,
} from './user';
import {
  DASHBOARD_COLLECTION,
  DASHBOARD_INDEXES,
  Dashboard,
} from './dashboard';
import {
  REPORT_COLLECTION,
  REPORT_INDEXES,
  ReportDocument,
} from './report';
import {
  ALERT_RULE_COLLECTION,
  ALERT_RULE_INDEXES,
  ALERT_HISTORY_COLLECTION,
  ALERT_HISTORY_INDEXES,
  AlertRule,
  AlertHistory,
} from './alert';
import {
  QUERY_HISTORY_COLLECTION,
  QUERY_HISTORY_INDEXES,
  QueryHistory,
} from './query';

/**
 * Initialize all MongoDB collections and indexes
 */
export async function initializeCollections(db: Db): Promise<void> {
  // Create collections if they don't exist
  const collections = await db.listCollections().toArray();
  const collectionNames = collections.map(c => c.name);

  const requiredCollections = [
    USER_COLLECTION,
    DASHBOARD_COLLECTION,
    REPORT_COLLECTION,
    ALERT_RULE_COLLECTION,
    ALERT_HISTORY_COLLECTION,
    QUERY_HISTORY_COLLECTION,
  ];

  for (const collectionName of requiredCollections) {
    if (!collectionNames.includes(collectionName)) {
      await db.createCollection(collectionName);
      console.log(`Created collection: ${collectionName}`);
    }
  }

  // Create indexes
  await createIndexes(db);
}

/**
 * Create indexes for all collections
 */
async function createIndexes(db: Db): Promise<void> {
  const indexConfigs = [
    { collection: USER_COLLECTION, indexes: USER_INDEXES },
    { collection: DASHBOARD_COLLECTION, indexes: DASHBOARD_INDEXES },
    { collection: REPORT_COLLECTION, indexes: REPORT_INDEXES },
    { collection: ALERT_RULE_COLLECTION, indexes: ALERT_RULE_INDEXES },
    { collection: ALERT_HISTORY_COLLECTION, indexes: ALERT_HISTORY_INDEXES },
    { collection: QUERY_HISTORY_COLLECTION, indexes: QUERY_HISTORY_INDEXES },
  ];

  for (const { collection, indexes } of indexConfigs) {
    const coll = db.collection(collection);
    
    for (const indexSpec of indexes) {
      try {
        await coll.createIndex(indexSpec.key, {
          unique: indexSpec.unique,
          sparse: indexSpec.sparse,
          name: indexSpec.name,
          expireAfterSeconds: (indexSpec as any).expireAfterSeconds,
        });
        console.log(`Created index ${indexSpec.name} on ${collection}`);
      } catch (error: any) {
        // Index might already exist
        if (error.code !== 85 && error.code !== 86) {
          console.error(`Error creating index ${indexSpec.name} on ${collection}:`, error);
        }
      }
    }
  }
}

/**
 * Get typed collection references
 */
export function getCollections(db: Db) {
  return {
    users: db.collection<UserProfile>(USER_COLLECTION),
    dashboards: db.collection<Dashboard>(DASHBOARD_COLLECTION),
    reports: db.collection<ReportDocument>(REPORT_COLLECTION),
    alertRules: db.collection<AlertRule>(ALERT_RULE_COLLECTION),
    alertHistory: db.collection<AlertHistory>(ALERT_HISTORY_COLLECTION),
    queryHistory: db.collection<QueryHistory>(QUERY_HISTORY_COLLECTION),
  };
}
