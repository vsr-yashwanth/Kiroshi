import enum


class UserRole(str, enum.Enum):
    TOURIST = "TOURIST"
    AUTHORITY = "AUTHORITY"
    RESPONDER = "RESPONDER"
    ADMIN = "ADMIN"


class TripStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EmergencyStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    AT_RISK = "AT_RISK"
    SOS = "SOS"


class GeoZoneType(str, enum.Enum):
    SAFE = "SAFE"
    RESTRICTED = "RESTRICTED"
    HIGH_RISK = "HIGH_RISK"
    CUSTOM = "CUSTOM"


class ZoneEventType(str, enum.Enum):
    ENTER = "ENTER"
    EXIT = "EXIT"


class LocationFreshness(str, enum.Enum):
    LIVE = "LIVE"
    RECENT = "RECENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

