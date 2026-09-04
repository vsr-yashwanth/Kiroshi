import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from backend.app.domain.models.enums import NotificationChannel, NotificationDeliveryStatus


class NotificationResponse(BaseModel):
    id: uuid.UUID
    recipient_id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    title: str
    message: str
    channel: NotificationChannel
    status: NotificationDeliveryStatus
    is_read: bool
    retry_count: int
    payload: Optional[Dict[str, Any]] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
