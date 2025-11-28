import { Db } from 'mongodb';

/**
 * Migration system types
 * Requirements: All data storage requirements
 */

export interface Migration {
  version: number;
  name: string;
  description: string;
  up: (db: Db) => Promise<void>;
  down: (db: Db) => Promise<void>;
}

export interface MigrationRecord {
  version: number;
  name: string;
  appliedAt: Date;
  executionTime: number;
}

export const MIGRATION_COLLECTION = '_migrations';
