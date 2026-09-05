"""
KIROSHI — Real-Time MongoDB Synchronization Layer

Listens to all database events and transparently replicates
every Tourist profile update, registration, SOS alert, trip,
and location telemetry point directly into MongoDB:
    mongodb://localhost:27017/Kiroshi
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import pymongo
from pymongo import MongoClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger

MONGO_URI = getattr(settings, "MONGO_URI", "mongodb://localhost:27017/Kiroshi")
MONGO_DB_NAME = getattr(settings, "MONGO_DB_NAME", "Kiroshi")

_client: Optional[MongoClient] = None
_db = None


def get_mongo_db():
    global _client, _db
    if _db is None:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            _db = _client[MONGO_DB_NAME]
        except Exception as exc:
            logger.warning("MongoDB connection not available: %s", exc)
            return None
    return _db


def _to_json_compatible(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (int, float, bool, str)):
        return obj
    if isinstance(obj, datetime):
        return obj.replace(tzinfo=timezone.utc) if obj.tzinfo is None else obj
    if hasattr(obj, "value"):  # Enums
        return obj.value
    if hasattr(obj, "hex"):  # UUID
        return str(obj)
    return str(obj)


def sync_model_to_mongo(target: Any, action: str = "upsert") -> None:
    """Sync a SQLAlchemy model instance directly to its corresponding MongoDB collection."""
    try:
        db = get_mongo_db()
        if db is None:
            return

        table_name = getattr(target, "__tablename__", None)
        if not table_name:
            return

        # Map table to collection name
        collection_name = table_name

        target_id = str(getattr(target, "id", None))
        if not target_id:
            return

        collection = db[collection_name]

        if action == "delete":
            collection.delete_one({"id": target_id})
            return

        # Extract columns
        doc: Dict[str, Any] = {}
        for col in target.__table__.columns:
            val = getattr(target, col.name, None)
            doc[col.name] = _to_json_compatible(val)

        # Handle GeoJSON coordinates for spatial entities
        if collection_name == "location_events" and "latitude" in doc and "longitude" in doc:
            if doc["latitude"] is not None and doc["longitude"] is not None:
                doc["location"] = {
                    "type": "Point",
                    "coordinates": [float(doc["longitude"]), float(doc["latitude"])],
                }

        # Handle tourist_profiles passport hash field mapping if needed
        if collection_name == "tourist_profiles" and "passport_or_id_hash" in doc:
            doc["passport_hash"] = doc.get("passport_or_id_hash") or "sha256_mock_hash"

        # Update timestamps
        now = datetime.now(timezone.utc)
        if "updated_at" not in doc or not doc["updated_at"]:
            doc["updated_at"] = now
        if "created_at" not in doc or not doc["created_at"]:
            doc["created_at"] = now

        # Upsert into MongoDB
        collection.update_one(
            {"id": target_id},
            {"$set": doc},
            upsert=True,
        )

    except Exception as exc:
        logger.warning("Failed to sync %s to MongoDB: %s", getattr(target, "__tablename__", type(target)), exc)


def register_mongo_sync_listeners(engine):
    """Attach SQLAlchemy ORM post-commit listeners to mirror everything to MongoDB in real-time."""
    from backend.app.core.database import Base

    @event.listens_for(Session, "after_flush")
    def after_flush_listener(session, flush_context):
        for target in session.new:
            sync_model_to_mongo(target, action="upsert")
        for target in session.dirty:
            sync_model_to_mongo(target, action="upsert")
        for target in session.deleted:
            sync_model_to_mongo(target, action="delete")
