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


class RiskLevel(str, enum.Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendedAction(str, enum.Enum):
    MONITOR = "MONITOR"
    REVIEW = "REVIEW"
    CONTACT_TOURIST = "CONTACT_TOURIST"
    ESCALATE_FOR_HUMAN_REVIEW = "ESCALATE_FOR_HUMAN_REVIEW"


class RiskSignalType(str, enum.Enum):
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    RESTRICTED_ZONE = "RESTRICTED_ZONE"
    HIGH_RISK_ZONE = "HIGH_RISK_ZONE"
    PROLONGED_INACTIVITY = "PROLONGED_INACTIVITY"
    UNUSUAL_SPEED = "UNUSUAL_SPEED"
    UNUSUAL_MOVEMENT = "UNUSUAL_MOVEMENT"
    ZONE_EVENT = "ZONE_EVENT"


