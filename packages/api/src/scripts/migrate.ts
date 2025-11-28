#!/usr/bin/env node
/**
 * Database migration CLI tool
 * 
 * Usage:
 *   npm run migrate status          - Show migration status
 *   npm run migrate up              - Apply all pending migrations
 *   npm run migrate down            - Rollback last migration
 *   npm run migrate to <version>    - Migrate to specific version
 */

import { connectMongoDB, closeMongoDB } from '../database/mongodb';
import { MigrationManager, allMigrations } from '../migrations';

async function main() {
  const command = process.argv[2];
  const arg = process.argv[3];

  try {
    const db = await connectMongoDB();
    const manager = new MigrationManager(db, allMigrations);

    switch (command) {
      case 'status': {
        const status = await manager.getStatus();
        console.log('\n=== Migration Status ===');
        console.log(`Current version: ${status.currentVersion}`);
        console.log(`Latest version: ${status.latestVersion}`);
        console.log(`\nApplied migrations (${status.appliedMigrations.length}):`);
        for (const migration of status.appliedMigrations) {
          console.log(
            `  ${migration.version}: ${migration.name} (${migration.appliedAt.toISOString()})`
          );
        }
        console.log(`\nPending migrations (${status.pendingMigrations.length}):`);
        for (const migration of status.pendingMigrations) {
          console.log(`  ${migration.version}: ${migration.name}`);
        }
        break;
      }

      case 'up': {
        await manager.migrateToLatest();
        break;
      }

      case 'down': {
        await manager.rollbackLast();
        break;
      }

      case 'to': {
        if (!arg) {
          console.error('Error: Version number required');
          console.log('Usage: npm run migrate to <version>');
          process.exit(1);
        }
        const version = parseInt(arg, 10);
        if (isNaN(version)) {
          console.error('Error: Invalid version number');
          process.exit(1);
        }
        await manager.migrateTo(version);
        break;
      }

      default: {
        console.log('Database Migration Tool\n');
        console.log('Usage:');
        console.log('  npm run migrate status          - Show migration status');
        console.log('  npm run migrate up              - Apply all pending migrations');
        console.log('  npm run migrate down            - Rollback last migration');
        console.log('  npm run migrate to <version>    - Migrate to specific version');
        break;
      }
    }

    await closeMongoDB();
    process.exit(0);
  } catch (error) {
    console.error('Migration failed:', error);
    await closeMongoDB();
    process.exit(1);
  }
}

main();
