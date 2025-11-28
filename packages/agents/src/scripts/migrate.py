#!/usr/bin/env python3
"""
Database migration CLI tool

Usage:
    python -m src.scripts.migrate status          - Show migration status
    python -m src.scripts.migrate up              - Apply all pending migrations
    python -m src.scripts.migrate down            - Rollback last migration
    python -m src.scripts.migrate to <version>    - Migrate to specific version
"""
import sys
import asyncio

from ..database.mongodb import connect_mongodb, close_mongodb
from ..migrations import MigrationManager, all_migrations


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    try:
        db = await connect_mongodb()
        manager = MigrationManager(db, all_migrations)

        if command == "status":
            await show_status(manager)
        elif command == "up":
            await manager.migrate_to_latest()
        elif command == "down":
            await manager.rollback_last()
        elif command == "to":
            if len(sys.argv) < 3:
                print("Error: Version number required")
                print("Usage: python -m src.scripts.migrate to <version>")
                sys.exit(1)
            try:
                version = int(sys.argv[2])
                await manager.migrate_to(version)
            except ValueError:
                print("Error: Invalid version number")
                sys.exit(1)
        else:
            print_usage()

        await close_mongodb()
    except Exception as e:
        print(f"Migration failed: {e}")
        await close_mongodb()
        sys.exit(1)


async def show_status(manager: MigrationManager):
    """Show migration status"""
    status = await manager.get_status()

    print("\n=== Migration Status ===")
    print(f"Current version: {status['current_version']}")
    print(f"Latest version: {status['latest_version']}")

    print(f"\nApplied migrations ({len(status['applied_migrations'])}):")
    for migration in status["applied_migrations"]:
        print(
            f"  {migration.version}: {migration.name} "
            f"({migration.applied_at.isoformat()})"
        )

    print(f"\nPending migrations ({len(status['pending_migrations'])}):")
    for migration in status["pending_migrations"]:
        print(f"  {migration.version}: {migration.name}")


def print_usage():
    """Print usage information"""
    print("Database Migration Tool\n")
    print("Usage:")
    print("  python -m src.scripts.migrate status          - Show migration status")
    print("  python -m src.scripts.migrate up              - Apply all pending migrations")
    print("  python -m src.scripts.migrate down            - Rollback last migration")
    print("  python -m src.scripts.migrate to <version>    - Migrate to specific version")


if __name__ == "__main__":
    asyncio.run(main())
