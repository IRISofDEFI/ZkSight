/**
 * Database migration system
 * Requirements: All data storage requirements
 */

export * from './types';
export * from './manager';

import { Migration } from './types';
import { migration001 } from './migrations/001_initial_schema';
import { migration002 } from './migrations/002_add_user_roles';

/**
 * All migrations in order
 * Add new migrations to this array
 */
export const allMigrations: Migration[] = [
  migration001,
  migration002,
];
