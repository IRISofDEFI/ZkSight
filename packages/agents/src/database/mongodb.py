"""MongoDB connection and initialization utilities"""
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, OperationFailure

from ..config import load_config
from ..models.user import USER_COLLECTION, USER_INDEXES
from ..models.dashboard import DASHBOARD_COLLECTION, DASHBOARD_INDEXES
from ..models.report import REPORT_COLLECTION, REPORT_INDEXES
from ..models.alert import (
    ALERT_RULE_COLLECTION,
    ALERT_RULE_INDEXES,
    ALERT_HISTORY_COLLECTION,
    ALERT_HISTORY_INDEXES,
)
from ..models.query import QUERY_HISTORY_COLLECTION, QUERY_HISTORY_INDEXES


_client: Optional[MongoClient] = None
_db: Optional[Database] = None


async def connect_mongodb() -> Database:
    """Connect to MongoDB and initialize collections"""
    global _client, _db
    
    if _db is not None:
        return _db
    
    config = load_config()
    
    try:
        _client = MongoClient(
            config.mongodb.uri,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=45000,
        )
        
        # Test connection
        _client.admin.command('ping')
        print("Connected to MongoDB")
        
        _db = _client[config.mongodb.database]
        
        # Initialize collections and indexes
        await initialize_collections(_db)
        
        return _db
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise


def get_mongodb() -> Database:
    """Get the MongoDB database instance"""
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongodb() first.")
    return _db


async def close_mongodb() -> None:
    """Close MongoDB connection"""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        print("MongoDB connection closed")


async def check_mongodb_health() -> bool:
    """Health check for MongoDB connection"""
    try:
        if _db is None:
            return False
        _db.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB health check failed: {e}")
        return False


async def initialize_collections(db: Database) -> None:
    """Initialize all MongoDB collections and indexes"""
    # Get existing collections
    existing_collections = db.list_collection_names()
    
    # Collections to create
    required_collections = [
        USER_COLLECTION,
        DASHBOARD_COLLECTION,
        REPORT_COLLECTION,
        ALERT_RULE_COLLECTION,
        ALERT_HISTORY_COLLECTION,
        QUERY_HISTORY_COLLECTION,
    ]
    
    # Create collections if they don't exist
    for collection_name in required_collections:
        if collection_name not in existing_collections:
            db.create_collection(collection_name)
            print(f"Created collection: {collection_name}")
    
    # Create indexes
    await _create_indexes(db)


async def _create_indexes(db: Database) -> None:
    """Create indexes for all collections"""
    index_configs = [
        (USER_COLLECTION, USER_INDEXES),
        (DASHBOARD_COLLECTION, DASHBOARD_INDEXES),
        (REPORT_COLLECTION, REPORT_INDEXES),
        (ALERT_RULE_COLLECTION, ALERT_RULE_INDEXES),
        (ALERT_HISTORY_COLLECTION, ALERT_HISTORY_INDEXES),
        (QUERY_HISTORY_COLLECTION, QUERY_HISTORY_INDEXES),
    ]
    
    for collection_name, indexes in index_configs:
        collection = db[collection_name]
        
        for index_spec in indexes:
            try:
                options = {
                    "name": index_spec["name"],
                }
                
                if "unique" in index_spec:
                    options["unique"] = index_spec["unique"]
                if "sparse" in index_spec:
                    options["sparse"] = index_spec["sparse"]
                if "expireAfterSeconds" in index_spec:
                    options["expireAfterSeconds"] = index_spec["expireAfterSeconds"]
                
                collection.create_index(
                    index_spec["keys"],
                    **options
                )
                print(f"Created index {index_spec['name']} on {collection_name}")
            except OperationFailure as e:
                # Index might already exist
                if e.code not in (85, 86):
                    print(f"Error creating index {index_spec['name']} on {collection_name}: {e}")
