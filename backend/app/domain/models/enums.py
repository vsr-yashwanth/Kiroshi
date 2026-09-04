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
