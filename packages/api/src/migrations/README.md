# Database Migration System

This directory contains the database migration system for MongoDB schema changes.

## Overview

The migration system provides:
- Version tracking for database schemas
- Forward migrations (up)
- Rollback capability (down)
- Migration history and status

## Usage

### TypeScript/Node.js (API Package)

```bash
# Show migration status
npm run migrate:status

# Apply all pending migrations
npm run migrate:up

# Rollback last migration
npm run migrate:down

# Migrate to specific version
npm run migrate to 3
```

### Python (Agents Package)

```bash
# Show migration status
python -m src.scripts.migrate status

# Apply all pending migrations
python -m src.scripts.migrate up

# Rollback last migration
python -m src.scripts.migrate down

# Migrate to specific version
python -m src.scripts.migrate to 3
```

## Creating New Migrations

### TypeScript

1. Create a new file in `migrations/` directory:

```typescript
// migrations/003_add_feature.ts
import { Db } from 'mongodb';
import { Migration } from '../types';

export const migration003: Migration = {
  version: 3,
  name: 'add_feature',
  description: 'Add new feature to the system',

  async up(db: Db): Promise<void> {
    // Forward migration logic
    await db.collection('users').updateMany(
      { feature: { $exists: false } },
      { $set: { feature: true } }
    );
  },

  async down(db: Db): Promise<void> {
    // Rollback logic
    await db.collection('users').updateMany(
      {},
      { $unset: { feature: '' } }
    );
  },
};
```

2. Add the migration to `index.ts`:

```typescript
import { migration003 } from './migrations/003_add_feature';

export const allMigrations: Migration[] = [
  migration001,
  migration002,
  migration003, // Add here
];
```

### Python

1. Create a new file in `migrations/migrations/` directory:

```python
# migrations/migrations/migration_003_add_feature.py
from pymongo.database import Database
from ..types import Migration

async def up(db: Database) -> None:
    """Add new feature"""
    result = db["users"].update_many(
        {"feature": {"$exists": False}},
        {"$set": {"feature": True}}
    )
    print(f"Added feature to {result.modified_count} users")

async def down(db: Database) -> None:
    """Remove feature"""
    result = db["users"].update_many(
        {},
        {"$unset": {"feature": ""}}
    )
    print(f"Removed feature from {result.modified_count} users")

migration_003 = Migration(
    version=3,
    name="add_feature",
    description="Add new feature to the system",
    up=up,
    down=down,
)
```

2. Add the migration to `migrations/migrations/__init__.py`:

```python
from .migration_003_add_feature import migration_003

all_migrations: List[Migration] = [
    migration_001,
    migration_002,
    migration_003,  # Add here
]
```

## Migration Best Practices

1. **Always test migrations** on a development database first
2. **Make migrations reversible** - always implement both `up` and `down`
3. **Keep migrations small** - one logical change per migration
4. **Never modify existing migrations** - create a new migration instead
5. **Use transactions** when possible for atomic operations
6. **Backup data** before running migrations in production
7. **Version numbers must be sequential** and unique

## Migration Tracking

Migrations are tracked in the `_migrations` collection:

```json
{
  "version": 1,
  "name": "initial_schema",
  "appliedAt": "2024-01-15T10:30:00.000Z",
  "executionTime": 1234
}
```

## Troubleshooting

### Migration Failed

If a migration fails:
1. Check the error message
2. Fix the issue in the migration code
3. Rollback if necessary: `npm run migrate:down`
4. Re-apply the migration: `npm run migrate:up`

### Inconsistent State

If the database is in an inconsistent state:
1. Check migration status: `npm run migrate:status`
2. Manually fix data if needed
3. Update migration tracking if necessary

### Production Migrations

For production:
1. Always backup the database first
2. Test migrations in staging environment
3. Schedule migrations during low-traffic periods
4. Monitor application logs during and after migration
5. Have a rollback plan ready
