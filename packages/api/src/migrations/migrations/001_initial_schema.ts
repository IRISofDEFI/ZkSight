import { Db } from 'mongodb';
import { Migration } from '../types';
import { initializeCollections } from '../../models';

/**
 * Initial schema migration
 * Creates all collections and indexes
 */
export const migration001: Migration = {
  version: 1,
  name: 'initial_schema',
  description: 'Create initial collections and indexes',

  async up(db: Db): Promise<void> {
    // Initialize all collections and indexes
    await initializeCollections(db);
  },

  async down(db: Db): Promise<void> {
    // Drop all collections
    const collections = [
      'users',
      'dashboards',
      'reports',
      'alert_rules',
      'alert_history',
      'query_history',
    ];

    for (const collection of collections) {
      try {
        await db.dropCollection(collection);
        console.log(`Dropped collection: ${collection}`);
      } catch (error: any) {
        // Collection might not exist
        if (error.code !== 26) {
          throw error;
        }
      }
    }
  },
};
