import { Db } from 'mongodb';
import { Migration, MigrationRecord, MIGRATION_COLLECTION } from './types';

/**
 * Database migration manager
 * Handles version tracking and migration execution
 */
export class MigrationManager {
  private db: Db;
  private migrations: Migration[];

  constructor(db: Db, migrations: Migration[]) {
    this.db = db;
    this.migrations = migrations.sort((a, b) => a.version - b.version);
  }

  /**
   * Initialize migration tracking collection
   */
  private async initializeMigrationCollection(): Promise<void> {
    const collections = await this.db.listCollections().toArray();
    const collectionNames = collections.map(c => c.name);

    if (!collectionNames.includes(MIGRATION_COLLECTION)) {
      await this.db.createCollection(MIGRATION_COLLECTION);
      await this.db.collection(MIGRATION_COLLECTION).createIndex(
        { version: 1 },
        { unique: true, name: 'idx_version' }
      );
      console.log('Created migration tracking collection');
    }
  }

  /**
   * Get current database version
   */
  async getCurrentVersion(): Promise<number> {
    await this.initializeMigrationCollection();

    const records = await this.db
      .collection<MigrationRecord>(MIGRATION_COLLECTION)
      .find()
      .sort({ version: -1 })
      .limit(1)
      .toArray();

    return records.length > 0 ? records[0].version : 0;
  }

  /**
   * Get all applied migrations
   */
  async getAppliedMigrations(): Promise<MigrationRecord[]> {
    await this.initializeMigrationCollection();

    return this.db
      .collection<MigrationRecord>(MIGRATION_COLLECTION)
      .find()
      .sort({ version: 1 })
      .toArray();
  }

  /**
   * Get pending migrations
   */
  async getPendingMigrations(): Promise<Migration[]> {
    const currentVersion = await this.getCurrentVersion();
    return this.migrations.filter(m => m.version > currentVersion);
  }

  /**
   * Apply a single migration
   */
  private async applyMigration(migration: Migration): Promise<void> {
    const startTime = Date.now();

    console.log(`Applying migration ${migration.version}: ${migration.name}`);

    try {
      await migration.up(this.db);

      const executionTime = Date.now() - startTime;

      await this.db.collection<MigrationRecord>(MIGRATION_COLLECTION).insertOne({
        version: migration.version,
        name: migration.name,
        appliedAt: new Date(),
        executionTime,
      });

      console.log(
        `Migration ${migration.version} applied successfully (${executionTime}ms)`
      );
    } catch (error) {
      console.error(`Failed to apply migration ${migration.version}:`, error);
      throw error;
    }
  }

  /**
   * Rollback a single migration
   */
  private async rollbackMigration(migration: Migration): Promise<void> {
    const startTime = Date.now();

    console.log(`Rolling back migration ${migration.version}: ${migration.name}`);

    try {
      await migration.down(this.db);

      await this.db
        .collection<MigrationRecord>(MIGRATION_COLLECTION)
        .deleteOne({ version: migration.version });

      const executionTime = Date.now() - startTime;

      console.log(
        `Migration ${migration.version} rolled back successfully (${executionTime}ms)`
      );
    } catch (error) {
      console.error(`Failed to rollback migration ${migration.version}:`, error);
      throw error;
    }
  }

  /**
   * Migrate to latest version
   */
  async migrateToLatest(): Promise<void> {
    const pending = await this.getPendingMigrations();

    if (pending.length === 0) {
      console.log('Database is up to date');
      return;
    }

    console.log(`Applying ${pending.length} pending migration(s)`);

    for (const migration of pending) {
      await this.applyMigration(migration);
    }

    console.log('All migrations applied successfully');
  }

  /**
   * Migrate to specific version
   */
  async migrateTo(targetVersion: number): Promise<void> {
    const currentVersion = await this.getCurrentVersion();

    if (targetVersion === currentVersion) {
      console.log(`Database is already at version ${targetVersion}`);
      return;
    }

    if (targetVersion > currentVersion) {
      // Migrate up
      const migrationsToApply = this.migrations.filter(
        m => m.version > currentVersion && m.version <= targetVersion
      );

      console.log(`Migrating up to version ${targetVersion}`);
      for (const migration of migrationsToApply) {
        await this.applyMigration(migration);
      }
    } else {
      // Migrate down
      const migrationsToRollback = this.migrations
        .filter(m => m.version > targetVersion && m.version <= currentVersion)
        .reverse();

      console.log(`Migrating down to version ${targetVersion}`);
      for (const migration of migrationsToRollback) {
        await this.rollbackMigration(migration);
      }
    }

    console.log(`Migration to version ${targetVersion} completed`);
  }

  /**
   * Rollback last migration
   */
  async rollbackLast(): Promise<void> {
    const currentVersion = await this.getCurrentVersion();

    if (currentVersion === 0) {
      console.log('No migrations to rollback');
      return;
    }

    const migration = this.migrations.find(m => m.version === currentVersion);

    if (!migration) {
      throw new Error(`Migration ${currentVersion} not found`);
    }

    await this.rollbackMigration(migration);
  }

  /**
   * Get migration status
   */
  async getStatus(): Promise<{
    currentVersion: number;
    latestVersion: number;
    appliedMigrations: MigrationRecord[];
    pendingMigrations: Migration[];
  }> {
    const currentVersion = await this.getCurrentVersion();
    const latestVersion =
      this.migrations.length > 0
        ? this.migrations[this.migrations.length - 1].version
        : 0;
    const appliedMigrations = await this.getAppliedMigrations();
    const pendingMigrations = await this.getPendingMigrations();

    return {
      currentVersion,
      latestVersion,
      appliedMigrations,
      pendingMigrations,
    };
  }
}
