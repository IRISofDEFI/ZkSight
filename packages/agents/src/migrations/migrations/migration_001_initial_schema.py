"""Initial schema migration"""
from pymongo.database import Database

from ...database.mongodb import initialize_collections
from ..types import Migration


async def up(db: Database) -> None:
    """Create initial collections and indexes"""
    await initialize_collections(db)


async def down(db: Database) -> None:
    """Drop all collections"""
    collections = [
        "users",
        "dashboards",
        "reports",
        "alert_rules",
        "alert_history",
        "query_history",
    ]

    for collection in collections:
        try:
            db.drop_collection(collection)
            print(f"Dropped collection: {collection}")
        except Exception as e:
            # Collection might not exist
            print(f"Could not drop collection {collection}: {e}")


migration_001 = Migration(
    version=1,
    name="initial_schema",
    description="Create initial collections and indexes",
    up=up,
    down=down,
)
