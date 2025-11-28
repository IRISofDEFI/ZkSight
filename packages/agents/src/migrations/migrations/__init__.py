"""All migrations"""
from typing import List

from ..types import Migration
from .migration_001_initial_schema import migration_001
from .migration_002_add_user_roles import migration_002

# All migrations in order
all_migrations: List[Migration] = [
    migration_001,
    migration_002,
]
