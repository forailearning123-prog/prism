from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.collaboration.models import (
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationChannel,
)
from app.collaboration.schemas import NotificationPreferenceUpdate


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str = "",
        context_type: Optional[str] = None,
        context_id: Optional[int] = None,
    ) -> Optional[Notification]:
        # Check user preferences
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type,
                NotificationPreference.channel == NotificationChannel.in_app,
                NotificationPreference.enabled == True,
            )
        )
        pref = result.scalar_one_or_none()

        # If no preference exists, default to enabled
        if pref is None:
            pass  # Default to sending
        elif not pref.enabled:
            return None

        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            context_type=context_type,
            context_id=context_id,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int, int]:
        query = select(Notification).where(Notification.user_id == user_id)

        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if notification_type:
            query = query.where(Notification.notification_type == NotificationType(notification_type))

        # Get unread count
        unread_query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total, unread_count

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def mark_all_as_read(self, user_id: int) -> int:
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()
        now = datetime.now(timezone.utc)
        for n in notifications:
            n.is_read = True
            n.read_at = now
        await self.db.commit()
        return len(notifications)

    async def get_unread_count(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0

    async def get_preferences(self, user_id: int) -> list[NotificationPreference]:
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_preference(self, user_id: int, data: NotificationPreferenceUpdate) -> NotificationPreference:
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == NotificationType(data.notification_type),
                NotificationPreference.channel == NotificationChannel(data.channel),
            )
        )
        pref = result.scalar_one_or_none()

        if pref:
            pref.enabled = data.enabled
        else:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=NotificationType(data.notification_type),
                channel=NotificationChannel(data.channel),
                enabled=data.enabled,
            )
            self.db.add(pref)

        await self.db.commit()
        await self.db.refresh(pref)
        return pref