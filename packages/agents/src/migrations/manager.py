"""Database migration manager"""
import time
from typing import List
from datetime import datetime

from pymongo.database import Database
from pymongo.errors import OperationFailure

from .types import Migration, MigrationRecord, MIGRATION_COLLECTION


class MigrationManager:
    """Manages database migrations"""

    def __init__(self, db: Database, migrations: List[Migration]):
        self.db = db
        self.migrations = sorted(migrations, key=lambda m: m.version)

    async def _initialize_migration_collection(self) -> None:
        """Initialize migration tracking collection"""
        collections = self.db.list_collection_names()

        if MIGRATION_COLLECTION not in collections:
            self.db.create_collection(MIGRATION_COLLECTION)
            self.db[MIGRATION_COLLECTION].create_index(
                [("version", 1)],
                unique=True,
                name="idx_version"
            )
            print("Created migration tracking collection")

    async def get_current_version(self) -> int:
        """Get current database version"""
        await self._initialize_migration_collection()

        records = list(
            self.db[MIGRATION_COLLECTION]
            .find()
            .sort("version", -1)
            .limit(1)
        )

        return records[0]["version"] if records else 0

    async def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get all applied migrations"""
        await self._initialize_migration_collection()

        records = self.db[MIGRATION_COLLECTION].find().sort("version", 1)
        return [MigrationRecord(**record) for record in records]

    async def get_pending_migrations(self) -> List[Migration]:
        """Get pending migrations"""
        current_version = await self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]

    async def _apply_migration(self, migration: Migration) -> None:
        """Apply a single migration"""
        start_time = time.time()

        print(f"Applying migration {migration.version}: {migration.name}")

        try:
            await migration.up(self.db)

            execution_time = time.time() - start_time

            self.db[MIGRATION_COLLECTION].insert_one({
                "version": migration.version,
                "name": migration.name,
                "applied_at": datetime.utcnow(),
                "execution_time": execution_time,
            })

            print(
                f"Migration {migration.version} applied successfully "
                f"({execution_time:.2f}s)"
            )
        except Exception as e:
            print(f"Failed to apply migration {migration.version}: {e}")
            raise

    async def _rollback_migration(self, migration: Migration) -> None:
        """Rollback a single migration"""
        start_time = time.time()

        print(f"Rolling back migration {migration.version}: {migration.name}")

        try:
            await migration.down(self.db)

            self.db[MIGRATION_COLLECTION].delete_one(
                {"version": migration.version}
            )

            execution_time = time.time() - start_time

            print(
                f"Migration {migration.version} rolled back successfully "
                f"({execution_time:.2f}s)"
            )
        except Exception as e:
            print(f"Failed to rollback migration {migration.version}: {e}")
            raise

    async def migrate_to_latest(self) -> None:
        """Migrate to latest version"""
        pending = await self.get_pending_migrations()

        if not pending:
            print("Database is up to date")
            return

        print(f"Applying {len(pending)} pending migration(s)")

        for migration in pending:
            await self._apply_migration(migration)

        print("All migrations applied successfully")

    async def migrate_to(self, target_version: int) -> None:
        """Migrate to specific version"""
        current_version = await self.get_current_version()

        if target_version == current_version:
            print(f"Database is already at version {target_version}")
            return

        if target_version > current_version:
            # Migrate up
            migrations_to_apply = [
                m for m in self.migrations
                if current_version < m.version <= target_version
            ]

            print(f"Migrating up to version {target_version}")
            for migration in migrations_to_apply:
                await self._apply_migration(migration)
        else:
            # Migrate down
            migrations_to_rollback = [
                m for m in reversed(self.migrations)
                if target_version < m.version <= current_version
            ]

            print(f"Migrating down to version {target_version}")
            for migration in migrations_to_rollback:
                await self._rollback_migration(migration)

        print(f"Migration to version {target_version} completed")

    async def rollback_last(self) -> None:
        """Rollback last migration"""
        current_version = await self.get_current_version()

        if current_version == 0:
            print("No migrations to rollback")
            return

        migration = next(
            (m for m in self.migrations if m.version == current_version),
            None
        )

        if not migration:
            raise ValueError(f"Migration {current_version} not found")

        await self._rollback_migration(migration)

    async def get_status(self) -> dict:
        """Get migration status"""
        current_version = await self.get_current_version()
        latest_version = (
            self.migrations[-1].version if self.migrations else 0
        )
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()

        return {
            "current_version": current_version,
            "latest_version": latest_version,
            "applied_migrations": applied_migrations,
            "pending_migrations": pending_migrations,
        }
