import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.auth import UserResponse


class TouristProfileBase(BaseModel):
    nationality: Optional[str] = Field(None, max_length=100)
    passport_or_id_hash: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)
    medical_notes: Optional[str] = None
    consent_given: bool = Field(default=False)


class TouristProfileCreate(TouristProfileBase):
    pass


class TouristProfileUpdate(BaseModel):
    nationality: Optional[str] = Field(None, max_length=100)
    passport_or_id_hash: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)
    medical_notes: Optional[str] = None
    consent_given: Optional[bool] = None


class TouristProfileResponse(TouristProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
