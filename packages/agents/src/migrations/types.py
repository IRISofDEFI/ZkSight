"""Migration system types"""
from typing import Callable, Awaitable
from datetime import datetime
from pydantic import BaseModel

from pymongo.database import Database


# Migration function type
MigrationFunc = Callable[[Database], Awaitable[None]]


class Migration(BaseModel):
    """Migration definition"""
    version: int
    name: str
    description: str
    up: MigrationFunc
    down: MigrationFunc

    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True


class MigrationRecord(BaseModel):
    """Migration record in database"""
    version: int
    name: str
    applied_at: datetime
    execution_time: float

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Collection name for migration tracking
MIGRATION_COLLECTION = "_migrations"
