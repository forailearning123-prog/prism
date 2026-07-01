import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AlertEvent, NotificationConfig, NotificationDelivery,
    NotificationChannelType, MonitorSeverity, User,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles notification delivery across multiple channels."""

    async def deliver(self, alert: AlertEvent, db: AsyncSession):
        """Deliver notification for an alert to all configured users."""
        try:
            # Get all users with notification configs matching the alert severity
            result = await db.execute(
                select(NotificationConfig)
                .where(
                    NotificationConfig.enabled == True,
                    NotificationConfig.min_severity <= alert.severity,
                )
            )
            configs = result.scalars().all()

            for config in configs:
                if self._is_quiet_hours(config):
                    continue

                delivery = NotificationDelivery(
                    alert_id=alert.id,
                    user_id=config.user_id,
                    channel=config.channel,
                    status="pending",
                )
                db.add(delivery)

                try:
                    await self._send_to_channel(config.channel, alert, config)
                    delivery.status = "delivered"
                    delivery.delivered_at = datetime.now(timezone.utc)
                except Exception as e:
                    delivery.status = "failed"
                    delivery.error_message = str(e)
                    logger.error(f"Notification delivery failed: {e}")

            await db.commit()

        except Exception as e:
            logger.error(f"Error delivering notifications for alert {alert.id}: {e}")

    async def _send_to_channel(self, channel: NotificationChannelType, alert: AlertEvent, config: NotificationConfig):
        """Send notification to a specific channel."""
        if channel == NotificationChannelType.in_app:
            # In-app notifications are stored as deliveries; no external call needed
            pass
        elif channel == NotificationChannelType.email:
            await self._send_email(alert, config)
        elif channel == NotificationChannelType.slack:
            await self._send_slack(alert, config)
        elif channel == NotificationChannelType.teams:
            await self._send_teams(alert, config)
        elif channel == NotificationChannelType.webhook:
            await self._send_webhook(alert, config)

    async def _send_email(self, alert: AlertEvent, config: NotificationConfig):
        """Send email notification."""
        webhook_url = config.config.get("webhook_url")
        if webhook_url:
            # In production, integrate with SendGrid, SES, etc.
            logger.info(f"Would send email to {config.user_id} for alert {alert.id}")

    async def _send_slack(self, alert: AlertEvent, config: NotificationConfig):
        """Send Slack notification."""
        webhook_url = config.config.get("webhook_url")
        if webhook_url:
            # In production, use Slack SDK to post message
            logger.info(f"Would send Slack to {config.user_id} for alert {alert.id}")

    async def _send_teams(self, alert: AlertEvent, config: NotificationConfig):
        """Send Microsoft Teams notification."""
        webhook_url = config.config.get("webhook_url")
        if webhook_url:
            # In production, use Teams connector
            logger.info(f"Would send Teams to {config.user_id} for alert {alert.id}")

    async def _send_webhook(self, alert: AlertEvent, config: NotificationConfig):
        """Send webhook notification."""
        webhook_url = config.config.get("webhook_url")
        if webhook_url:
            # In production, use httpx to POST payload
            logger.info(f"Would send webhook to {config.user_id} for alert {alert.id}")

    def _is_quiet_hours(self, config: NotificationConfig) -> bool:
        """Check if current time is within quiet hours."""
        if not config.quiet_hours_start or not config.quiet_hours_end:
            return False
        now = datetime.now(timezone.utc)
        current_time = now.strftime("%H:%M")
        return config.quiet_hours_start <= current_time <= config.quiet_hours_end

    async def get_user_notifications(
        self,
        user_id: int,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NotificationDelivery], int]:
        """Get notifications for a user."""
        query = (
            select(NotificationDelivery)
            .where(NotificationDelivery.user_id == user_id)
            .order_by(NotificationDelivery.created_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def mark_as_read(self, delivery_id: int, db: AsyncSession) -> Optional[NotificationDelivery]:
        """Mark a notification as read."""
        delivery = await db.get(NotificationDelivery, delivery_id)
        if not delivery:
            return None
        delivery.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(delivery)
        return delivery

    async def get_unread_count(self, user_id: int, db: AsyncSession) -> int:
        """Get count of unread notifications for a user."""
        count = await db.scalar(
            select(func.count(NotificationDelivery.id))
            .where(
                NotificationDelivery.user_id == user_id,
                NotificationDelivery.read_at.is_(None),
            )
        )
        return count or 0