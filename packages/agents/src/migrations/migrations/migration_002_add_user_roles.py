"""Add user roles field migration"""
from pymongo.database import Database

from ..types import Migration


async def up(db: Database) -> None:
    """Add roles field to user profiles"""
    result = db["users"].update_many(
        {"roles": {"$exists": False}},
        {"$set": {"roles": ["user"]}}
    )
    print(f"Added roles field to {result.modified_count} user profiles")


async def down(db: Database) -> None:
    """Remove roles field from user profiles"""
    result = db["users"].update_many(
        {},
        {"$unset": {"roles": ""}}
    )
    print(f"Removed roles field from {result.modified_count} user profiles")


migration_002 = Migration(
    version=2,
    name="add_user_roles",
    description="Add roles field to user profiles",
    up=up,
    down=down,
)
