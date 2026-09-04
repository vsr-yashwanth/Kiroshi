import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.core.logging import logger
from backend.app.domain.models.notification import Notification
from backend.app.domain.models.enums import NotificationChannel, NotificationDeliveryStatus, UserRole
from backend.app.domain.models.user import User


class BaseNotificationProvider(ABC):
    @abstractmethod
    async def deliver(self, notification: Notification) -> bool:
        """Deliver notification payload. Returns True if successful, False otherwise."""
        pass


class InAppNotificationProvider(BaseNotificationProvider):
    """
    In-app notification delivery provider.
    Marks notifications as SENT and available for API query and dashboard/mobile display.
    """
    async def deliver(self, notification: Notification) -> bool:
        try:
            notification.status = NotificationDeliveryStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            return True
        except Exception as e:
            logger.error(f"InAppNotificationProvider error: {e}")
            notification.status = NotificationDeliveryStatus.FAILED
            return False


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        # Provider registry by channel
        self._providers: Dict[NotificationChannel, BaseNotificationProvider] = {
            NotificationChannel.IN_APP: InAppNotificationProvider(),
        }

    async def notify_user(
        self,
        recipient_id: uuid.UUID,
        title: str,
        message: str,
        incident_id: Optional[uuid.UUID] = None,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        idempotency_key: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        """
        Sends a notification to a specific recipient with idempotency and fault isolation.
        Failure to deliver does NOT throw to protect primary business transactions.
        """
        try:
            # 1. Idempotency check
            if idempotency_key:
                existing = self.db.execute(
                    select(Notification).where(Notification.idempotency_key == idempotency_key)
                ).scalar_one_or_none()
                if existing:
                    logger.info(f"Duplicate notification suppressed by idempotency_key: {idempotency_key}")
                    return existing

            # 2. Create notification record
            notification = Notification(
                recipient_id=recipient_id,
                incident_id=incident_id,
                title=title,
                message=message,
                channel=channel,
                status=NotificationDeliveryStatus.PENDING,
                idempotency_key=idempotency_key,
                payload=payload or {},
            )
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            # 3. Deliver via configured provider
            provider = self._providers.get(channel, self._providers[NotificationChannel.IN_APP])
            success = await provider.deliver(notification)
            if success:
                notification.status = NotificationDeliveryStatus.SENT
            else:
                notification.status = NotificationDeliveryStatus.FAILED
                notification.retry_count += 1

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            return notification

        except Exception as e:
            logger.error(f"Failed to process notification for user {recipient_id}: {e}")
            # Note: Do NOT re-raise. Primary transaction (e.g. incident creation) must proceed!
            return None

    async def notify_authorities(
        self,
        title: str,
        message: str,
        incident_id: Optional[uuid.UUID] = None,
        idempotency_prefix: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> List[Notification]:
        """Notifies all active Authority and Admin users."""
        authorities = list(
            self.db.execute(
                select(User).where(
                    and_(
                        User.role.in_([UserRole.AUTHORITY, UserRole.ADMIN]),
                        User.is_active == True,
                    )
                )
            ).scalars().all()
        )

        sent_notifications = []
        for auth in authorities:
            key = f"{idempotency_prefix}_{auth.id}" if idempotency_prefix else None
            notif = await self.notify_user(
                recipient_id=auth.id,
                title=title,
                message=message,
                incident_id=incident_id,
                channel=NotificationChannel.IN_APP,
                idempotency_key=key,
                payload=payload,
            )
            if notif:
                sent_notifications.append(notif)
        return sent_notifications

    def list_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        filters = [Notification.recipient_id == user_id]
        if unread_only:
            filters.append(Notification.is_read == False)

        stmt = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Notification]:
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
            )
        )
        notif = self.db.execute(stmt).scalar_one_or_none()
        if notif:
            notif.is_read = True
            self.db.add(notif)
            self.db.commit()
            self.db.refresh(notif)
        return notif
