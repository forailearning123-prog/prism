import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AlertEvent, AlertStatus, EscalationPolicy, EscalationStep,
    EscalationLevel, NotificationDelivery, NotificationChannelType,
)

logger = logging.getLogger(__name__)


class EscalationService:
    """Manages alert escalation policies."""

    async def check(self, alert: AlertEvent, db: AsyncSession):
        """Check if an alert needs escalation."""
        if alert.status == AlertStatus.resolved:
            return

        # Find applicable escalation policies
        result = await db.execute(
            select(EscalationPolicy)
            .where(
                EscalationPolicy.is_active == True,
                EscalationPolicy.monitor_id == alert.monitor_id,
            )
            .options(selectinload(EscalationPolicy.steps))
        )
        policies = result.scalars().all()

        for policy in policies:
            await self._apply_policy(policy, alert, db)

    async def _apply_policy(self, policy: EscalationPolicy, alert: AlertEvent, db: AsyncSession):
        """Apply an escalation policy to an alert."""
        now = datetime.now(timezone.utc)
        elapsed = (now - alert.created_at).total_seconds() / 60  # minutes

        for step in policy.steps:
            if elapsed >= step.delay_minutes and step.level_order > (alert.escalation_count or 0):
                alert.escalation_level = step.level
                alert.escalation_count = step.level_order

                # Create escalation notification
                delivery = NotificationDelivery(
                    alert_id=alert.id,
                    user_id=step.notify_user_id or 0,
                    channel=NotificationChannelType.in_app,
                    status="escalated",
                )
                db.add(delivery)
                await db.commit()
                logger.info(
                    f"Escalated alert {alert.id} to level {step.level.value} "
                    f"(delay: {step.delay_minutes}m, elapsed: {elapsed:.0f}m)"
                )
                break