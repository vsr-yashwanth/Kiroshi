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


class IncidentSource(str, enum.Enum):
    SOS = "SOS"
    RISK_ENGINE = "RISK_ENGINE"
    AUTHORITY = "AUTHORITY"
    SYSTEM = "SYSTEM"


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    ESCALATED = "ESCALATED"
    ASSIGNED = "ASSIGNED"
    RESPONDING = "RESPONDING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    DISMISSED = "DISMISSED"


class IncidentEventType(str, enum.Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    INCIDENT_VERIFIED = "INCIDENT_VERIFIED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    INCIDENT_ASSIGNED = "INCIDENT_ASSIGNED"
    RESPONSE_STARTED = "RESPONSE_STARTED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"
    INCIDENT_CLOSED = "INCIDENT_CLOSED"
    INCIDENT_DISMISSED = "INCIDENT_DISMISSED"


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REASSIGNED = "REASSIGNED"
    CANCELLED = "CANCELLED"


class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"


class NotificationDeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    RETRYING = "RETRYING"



