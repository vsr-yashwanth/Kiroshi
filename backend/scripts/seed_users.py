import sys
import os
from typing import Any, Dict, List
from datetime import datetime, timezone, timedelta

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.trip import Trip
from backend.app.domain.models.itinerary import Itinerary
from backend.app.domain.models.enums import UserRole, TripStatus, EmergencyStatus


def seed() -> None:
    db = SessionLocal()
    try:
        print("[SEED] Seeding KIROSHI database with demo users and active trip...")

        users_data: List[Dict[str, Any]] = [
            {
                "email": "superadmin@kiroshi.org",
                "password": "Password123!",
                "full_name": "Super Administrator",
                "role": UserRole.ADMIN,
                "phone_number": "+1-800-555-0001",
            },
            {
                "email": "admin@kiroshi.org",
                "password": "Password123!",
                "full_name": "System Administrator",
                "role": UserRole.ADMIN,
                "phone_number": "+1-800-555-0002",
            },
            {
                "email": "authority@kiroshi.org",
                "password": "Password123!",
                "full_name": "Commander Shepard",
                "role": UserRole.AUTHORITY,
                "phone_number": "+1-800-555-0003",
            },
            {
                "email": "yashwanth@kiroshi.org",
                "password": "Password123!",
                "full_name": "Yashwanth (Tourist)",
                "role": UserRole.TOURIST,
                "phone_number": "+91-9876543210",
                "profile": {
                    "nationality": "Indian",
                    "emergency_contact_name": "Emergency Services",
                    "emergency_contact_phone": "+91-9876543211",
                    "medical_notes": "None. Blood Group O+",
                    "consent_given": True,
                },
                "trip": {
                    "title": "Himalayan Foothills Exploration",
                    "description": "Scenic mountain trail and cultural heritage journey",
                    "waypoints": [
                        {"name": "Dehradun Base Camp", "lat": 30.3165, "lon": 78.0322, "order": 1},
                        {"name": "Mussoorie Ridge", "lat": 30.4598, "lon": 78.0644, "order": 2},
                        {"name": "Dhanaulti Eco Park", "lat": 30.4180, "lon": 78.2390, "order": 3},
                    ],
                },
            },
        ]

        created_users: List[User] = []
        now = datetime.now(timezone.utc)

        for u_data in users_data:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if existing:
                print(f"  [INFO] User {u_data['email']} already exists (skipping creation).")
                created_users.append(existing)
                continue

            user = User(
                email=u_data["email"],
                hashed_password=get_password_hash(u_data["password"]),
                full_name=u_data["full_name"],
                phone_number=u_data["phone_number"],
                role=u_data["role"],
                is_active=True,
            )
            db.add(user)
            db.flush()

            if "profile" in u_data and isinstance(u_data["profile"], dict):
                prof_data: Dict[str, Any] = u_data["profile"]
                profile = TouristProfile(
                    user_id=user.id,
                    nationality=prof_data["nationality"],
                    emergency_contact_name=prof_data["emergency_contact_name"],
                    emergency_contact_phone=prof_data["emergency_contact_phone"],
                    medical_notes=prof_data["medical_notes"],
                    consent_given=prof_data["consent_given"],
                )
                db.add(profile)

            if "trip" in u_data and isinstance(u_data["trip"], dict):
                trip_data: Dict[str, Any] = u_data["trip"]
                trip = Trip(
                    tourist_id=user.id,
                    title=trip_data["title"],
                    description=trip_data["description"],
                    start_date=now - timedelta(hours=2),
                    end_date=now + timedelta(days=5),
                    status=TripStatus.ACTIVE,
                    emergency_status=EmergencyStatus.NORMAL,
                )
                db.add(trip)
                db.flush()

                waypoints: List[Dict[str, Any]] = trip_data.get("waypoints", [])
                for wp in waypoints:
                    itinerary = Itinerary(
                        trip_id=trip.id,
                        destination_name=wp["name"],
                        latitude=wp["lat"],
                        longitude=wp["lon"],
                        sequence_order=wp["order"],
                        planned_arrival=now + timedelta(hours=wp["order"] * 4),
                        planned_departure=now + timedelta(hours=wp["order"] * 8),
                    )
                    db.add(itinerary)

            db.commit()
            print(f"  [OK] Created user: {user.email} (Role: {user.role.value})")
            created_users.append(user)

        print("\n[SUCCESS] Database successfully seeded with accounts!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
