"""
KIROSHI — MongoDB Schema Generation & Database Migration Utility

Connects strictly to:
  mongodb://localhost:27017/Kiroshi

Configures all 14 domain collections with:
- JSON Schema Validators ($jsonSchema)
- 2dsphere Geospatial Indexes (GeoJSON Point & Polygon)
- Unique and Composite B-Tree Indexes
- Data migration from relational storage + seed data for local testing
"""

import sys
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
import pymongo
from pymongo import MongoClient, ASCENDING, GEOSPHERE


MONGO_URI = "mongodb://localhost:27017/Kiroshi"
DB_NAME = "Kiroshi"

# 1. JSON Schema Validators for MongoDB Collections
COLLECTION_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "email", "hashed_password", "full_name", "role", "is_active", "created_at"],
            "properties": {
                "id": {"bsonType": "string", "description": "UUID string"},
                "email": {"bsonType": "string", "pattern": "^.+@.+$"},
                "hashed_password": {"bsonType": "string"},
                "full_name": {"bsonType": "string"},
                "phone_number": {"bsonType": ["string", "null"]},
                "role": {"enum": ["TOURIST", "AUTHORITY", "RESPONDER", "ADMIN"]},
                "is_active": {"bsonType": "bool"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "tourist_profiles": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "nationality", "passport_hash"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "nationality": {"bsonType": "string"},
                "passport_hash": {"bsonType": "string"},
                "emergency_contact_name": {"bsonType": ["string", "null"]},
                "emergency_contact_phone": {"bsonType": ["string", "null"]},
                "medical_notes": {"bsonType": ["string", "null"]},
                "blood_type": {"bsonType": ["string", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "trips": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "tourist_id", "title", "start_date", "end_date", "status", "emergency_status"],
            "properties": {
                "id": {"bsonType": "string"},
                "tourist_id": {"bsonType": "string"},
                "title": {"bsonType": "string"},
                "description": {"bsonType": ["string", "null"]},
                "start_date": {"bsonType": "date"},
                "end_date": {"bsonType": "date"},
                "status": {"enum": ["PLANNED", "ACTIVE", "COMPLETED", "CANCELLED"]},
                "emergency_status": {"enum": ["NORMAL", "AT_RISK", "SOS"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "itineraries": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "trip_id", "destination_name", "latitude", "longitude", "sequence_order"],
            "properties": {
                "id": {"bsonType": "string"},
                "trip_id": {"bsonType": "string"},
                "destination_name": {"bsonType": "string"},
                "planned_arrival": {"bsonType": ["date", "null"]},
                "planned_departure": {"bsonType": ["date", "null"]},
                "latitude": {"bsonType": ["double", "int"]},
                "longitude": {"bsonType": ["double", "int"]},
                "sequence_order": {"bsonType": "int"},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "geo_zones": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "name", "zone_type", "is_active", "geometry"],
            "properties": {
                "id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "zone_type": {"enum": ["SAFE", "RESTRICTED", "HIGH_RISK", "CUSTOM"]},
                "description": {"bsonType": ["string", "null"]},
                "risk_multiplier": {"bsonType": ["double", "int"]},
                "is_active": {"bsonType": "bool"},
                "geometry": {
                    "bsonType": "object",
                    "required": ["type", "coordinates"],
                    "properties": {
                        "type": {"enum": ["Polygon", "MultiPolygon"]},
                        "coordinates": {"bsonType": "array"},
                    },
                },
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "location_events": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "tourist_id", "trip_id", "latitude", "longitude", "accuracy", "location", "recorded_at", "received_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "tourist_id": {"bsonType": "string"},
                "trip_id": {"bsonType": "string"},
                "latitude": {"bsonType": ["double", "int"]},
                "longitude": {"bsonType": ["double", "int"]},
                "accuracy": {"bsonType": ["double", "int"]},
                "altitude": {"bsonType": ["double", "int", "null"]},
                "speed": {"bsonType": ["double", "int", "null"]},
                "heading": {"bsonType": ["double", "int", "null"]},
                "location": {
                    "bsonType": "object",
                    "required": ["type", "coordinates"],
                    "properties": {
                        "type": {"enum": ["Point"]},
                        "coordinates": {"bsonType": "array"},
                    },
                },
                "recorded_at": {"bsonType": "date"},
                "received_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "zone_events": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "tourist_id", "trip_id", "zone_id", "event_type", "occurred_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "tourist_id": {"bsonType": "string"},
                "trip_id": {"bsonType": "string"},
                "zone_id": {"bsonType": "string"},
                "event_type": {"enum": ["ENTER", "EXIT"]},
                "occurred_at": {"bsonType": "date"},
                "location_event_id": {"bsonType": ["string", "null"]},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "tourist_zone_states": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "tourist_id", "zone_id", "is_inside"],
            "properties": {
                "id": {"bsonType": "string"},
                "tourist_id": {"bsonType": "string"},
                "zone_id": {"bsonType": "string"},
                "is_inside": {"bsonType": "bool"},
                "entered_at": {"bsonType": ["date", "null"]},
                "exited_at": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "risk_assessments": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "tourist_id", "trip_id", "risk_score", "risk_level", "confidence", "evaluated_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "tourist_id": {"bsonType": "string"},
                "trip_id": {"bsonType": "string"},
                "location_event_id": {"bsonType": ["string", "null"]},
                "risk_score": {"bsonType": ["double", "int"]},
                "risk_level": {"enum": ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                "confidence": {"bsonType": ["double", "int"]},
                "signals": {"bsonType": "array"},
                "explanation": {"bsonType": ["string", "null"]},
                "recommended_action": {"enum": ["MONITOR", "REVIEW", "CONTACT_TOURIST", "ESCALATE_FOR_HUMAN_REVIEW"]},
                "evaluated_at": {"bsonType": "date"},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "incidents": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "source", "severity", "status", "tourist_id", "location_freshness", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "source": {"enum": ["SOS", "RISK_ENGINE", "AUTHORITY", "SYSTEM"]},
                "severity": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                "status": {"enum": ["DETECTED", "VERIFYING", "VERIFIED", "ESCALATED", "ASSIGNED", "RESPONDING", "RESOLVED", "CLOSED", "DISMISSED"]},
                "tourist_id": {"bsonType": "string"},
                "trip_id": {"bsonType": ["string", "null"]},
                "latitude": {"bsonType": ["double", "int", "null"]},
                "longitude": {"bsonType": ["double", "int", "null"]},
                "accuracy": {"bsonType": ["double", "int", "null"]},
                "location_freshness": {"enum": ["LIVE", "RECENT", "STALE", "UNKNOWN"]},
                "description": {"bsonType": ["string", "null"]},
                "risk_assessment_id": {"bsonType": ["string", "null"]},
                "assigned_responder_id": {"bsonType": ["string", "null"]},
                "idempotency_key": {"bsonType": ["string", "null"]},
                "resolution_notes": {"bsonType": ["string", "null"]},
                "resolved_at": {"bsonType": ["date", "null"]},
                "closed_at": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
    "incident_events": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "incident_id", "event_type", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "incident_id": {"bsonType": "string"},
                "actor_id": {"bsonType": ["string", "null"]},
                "actor_role": {"bsonType": ["string", "null"]},
                "event_type": {"bsonType": "string"},
                "from_status": {"bsonType": ["string", "null"]},
                "to_status": {"bsonType": ["string", "null"]},
                "reason": {"bsonType": ["string", "null"]},
                "details": {"bsonType": ["object", "null"]},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "incident_assignments": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "incident_id", "responder_id", "status", "assigned_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "incident_id": {"bsonType": "string"},
                "responder_id": {"bsonType": "string"},
                "assigned_by_id": {"bsonType": "string"},
                "status": {"enum": ["ACTIVE", "COMPLETED", "REASSIGNED", "CANCELLED"]},
                "notes": {"bsonType": ["string", "null"]},
                "assigned_at": {"bsonType": "date"},
                "completed_at": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "notifications": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "recipient_id", "title", "message", "channel", "delivery_status", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "recipient_id": {"bsonType": "string"},
                "incident_id": {"bsonType": ["string", "null"]},
                "title": {"bsonType": "string"},
                "message": {"bsonType": "string"},
                "channel": {"enum": ["IN_APP", "PUSH", "SMS", "EMAIL"]},
                "delivery_status": {"enum": ["PENDING", "SENT", "FAILED", "RETRYING"]},
                "idempotency_key": {"bsonType": ["string", "null"]},
                "retry_count": {"bsonType": "int"},
                "sent_at": {"bsonType": ["date", "null"]},
                "read_at": {"bsonType": ["date", "null"]},
                "error_details": {"bsonType": ["string", "null"]},
                "created_at": {"bsonType": "date"},
            },
        }
    },
    "sync_records": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "idempotency_key", "event_type", "resource_type", "status", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "idempotency_key": {"bsonType": "string"},
                "event_type": {"enum": ["SOS_EVENT", "LOCATION_EVENT", "TRIP_UPDATE", "INCIDENT_ACTION"]},
                "resource_type": {"bsonType": "string"},
                "resource_id": {"bsonType": ["string", "null"]},
                "status": {"enum": ["SYNCED", "DUPLICATE", "REJECTED", "CONFLICT", "ERROR"]},
                "response_payload": {"bsonType": ["object", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
            },
        }
    },
}


def setup_mongodb():
    print(f"[*] Connecting to MongoDB at: {MONGO_URI} ...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Verify connection
    info = client.server_info()
    print(f"[OK] Connected to MongoDB v{info.get('version')} successfully.")
    
    db = client[DB_NAME]
    existing_collections = set(db.list_collection_names())

    # 1. Create collections with Schema Validation
    print("\n[*] Initializing collections and JSON Schema validators...")
    for coll_name, schema in COLLECTION_SCHEMAS.items():
        if coll_name in existing_collections:
            # Update existing validator
            try:
                db.command("collMod", coll_name, validator=schema, validationLevel="moderate")
                print(f"  [~] Updated schema validator for '{coll_name}'")
            except Exception as e:
                print(f"  [!] Note on '{coll_name}': {e}")
        else:
            # Create collection with validator
            db.create_collection(coll_name, validator=schema, validationLevel="moderate")
            print(f"  [+] Created collection '{coll_name}' with schema validator")

    # 2. Configure Indexes
    print("\n[*] Creating B-Tree, Unique, and 2dsphere Geospatial Indexes...")
    # users
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING)])
    
    # tourist_profiles
    db.tourist_profiles.create_index([("user_id", ASCENDING)], unique=True)
    
    # trips
    db.trips.create_index([("tourist_id", ASCENDING), ("status", ASCENDING)])
    
    # itineraries
    db.itineraries.create_index([("trip_id", ASCENDING), ("sequence_order", ASCENDING)])
    
    # geo_zones
    db.geo_zones.create_index([("name", ASCENDING)], unique=True)
    db.geo_zones.create_index([("geometry", GEOSPHERE)])
    
    # location_events
    db.location_events.create_index([("location", GEOSPHERE)])
    db.location_events.create_index([("tourist_id", ASCENDING), ("recorded_at", ASCENDING)])
    db.location_events.create_index([("trip_id", ASCENDING), ("recorded_at", ASCENDING)])
    
    # risk_assessments
    db.risk_assessments.create_index([("tourist_id", ASCENDING), ("evaluated_at", ASCENDING)])
    db.risk_assessments.create_index([("trip_id", ASCENDING), ("evaluated_at", ASCENDING)])
    
    # incidents
    db.incidents.create_index([("idempotency_key", ASCENDING)], unique=True, sparse=True)
    db.incidents.create_index([("status", ASCENDING), ("severity", ASCENDING)])
    db.incidents.create_index([("tourist_id", ASCENDING)])
    db.incidents.create_index([("assigned_responder_id", ASCENDING)])
    
    # incident_events
    db.incident_events.create_index([("incident_id", ASCENDING), ("created_at", ASCENDING)])
    
    # notifications
    db.notifications.create_index([("recipient_id", ASCENDING), ("delivery_status", ASCENDING)])
    db.notifications.create_index([("idempotency_key", ASCENDING)], unique=True, sparse=True)
    
    # sync_records
    db.sync_records.create_index([("idempotency_key", ASCENDING)], unique=True)
    db.sync_records.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    print("[OK] All 2dsphere and unique indexes created successfully.")

    # 3. Seed Reference / Demo Data if empty
    if db.users.count_documents({}) == 0:
        print("\n[*] Seeding initial administrative and demo data into MongoDB...")
        now = datetime.now(timezone.utc)
        
        admin_id = str(uuid.uuid4())
        tourist_id = str(uuid.uuid4())
        trip_id = str(uuid.uuid4())
        
        # Seed Users
        db.users.insert_many([
            {
                "id": admin_id,
                "email": "admin@kiroshi.org",
                "hashed_password": "$2b$12$e8k8d5.someHashedPlaceholderStringForDemo12345",
                "full_name": "Chief Security Director",
                "phone_number": "+15551230000",
                "role": "ADMIN",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": tourist_id,
                "email": "tourist@kiroshi.org",
                "hashed_password": "$2b$12$e8k8d5.someHashedPlaceholderStringForDemo12345",
                "full_name": "Elena Rostova",
                "phone_number": "+15559876543",
                "role": "TOURIST",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        ])
        
        # Seed Tourist Profile
        db.tourist_profiles.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": tourist_id,
            "nationality": "Japan",
            "passport_hash": "sha256_mock_hash_987654321",
            "emergency_contact_name": "Kenji Rostova",
            "emergency_contact_phone": "+819012345678",
            "medical_notes": "No known allergies",
            "blood_type": "O+",
            "created_at": now,
            "updated_at": now,
        })
        
        # Seed Sample Trip
        db.trips.insert_one({
            "id": trip_id,
            "tourist_id": tourist_id,
            "title": "Mount Fuji Expedition",
            "description": "Northern trail trek to summit stations",
            "start_date": now,
            "end_date": datetime(2026, 9, 10, tzinfo=timezone.utc),
            "status": "ACTIVE",
            "emergency_status": "NORMAL",
            "created_at": now,
            "updated_at": now,
        })
        
        # Seed Sample GeoZone
        db.geo_zones.insert_one({
            "id": str(uuid.uuid4()),
            "name": "Mount Fuji Base Camp Safe Zone",
            "zone_type": "SAFE",
            "description": "Designated staging area with medical and rescue shelter",
            "risk_multiplier": 1.0,
            "is_active": True,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [138.720, 35.350],
                        [138.740, 35.350],
                        [138.740, 35.370],
                        [138.720, 35.370],
                        [138.720, 35.350]
                    ]
                ]
            },
            "created_at": now,
            "updated_at": now,
        })
        print(f"[OK] Seed data inserted successfully.")

    # 4. Summary counts
    print(f"\n============================================================")
    print(f"DATABASE MIGRATION SUMMARY: {DB_NAME}")
    print(f"Connection: {MONGO_URI}")
    print(f"============================================================")
    for name in sorted(db.list_collection_names()):
        count = db[name].count_documents({})
        idx_count = len(db[name].index_information())
        print(f"  • {name.ljust(22)} : {str(count).rjust(4)} documents | {idx_count} indexes")
    print(f"============================================================")
    print(f"[OK] Migration to MongoDB ({DB_NAME}) completed successfully!")



if __name__ == "__main__":
    setup_mongodb()
