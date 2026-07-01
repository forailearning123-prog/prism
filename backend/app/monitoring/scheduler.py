import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ScheduledInsight, InsightDeliveryHistory

logger = logging.getLogger(__name__)


class InsightScheduler:
    """Manages scheduled insight generation and delivery."""

    async def process_due(self, db: AsyncSession):
        """Process all scheduled insights that are due for generation."""
        result = await db.execute(
            select(ScheduledInsight)
            .where(
                ScheduledInsight.is_active == True,
            )
        )
        insights = result.scalars().all()

        now = datetime.now(timezone.utc)

        for insight in insights:
            try:
                if self._is_due(insight, now):
                    await self._generate_and_deliver(insight, db)
            except Exception as e:
                logger.error(f"Error processing scheduled insight {insight.id}: {e}")

    def _is_due(self, insight: ScheduledInsight, now: datetime) -> bool:
        """Check if a scheduled insight is due to run."""
        if not insight.next_run_at:
            return True
        return now >= insight.next_run_at

    async def _generate_and_deliver(self, insight: ScheduledInsight, db: AsyncSession):
        """Generate and deliver a scheduled insight."""
        content = await self._generate_content(insight, db)

        delivery = InsightDeliveryHistory(
            insight_id=insight.id,
            status="sent",
            recipient_count=len(insight.recipients),
            content_summary=content.get("summary", "")[:500] if content else "",
        )
        db.add(delivery)

        insight.last_generated_at = datetime.now(timezone.utc)
        insight.next_run_at = self._calculate_next_run(insight)

        await db.commit()
        logger.info(f"Delivered scheduled insight '{insight.name}' to {len(insight.recipients)} recipients")

    async def _generate_content(self, insight: ScheduledInsight, db: AsyncSession) -> Optional[dict]:
        """Generate the content for a scheduled insight."""
        # In production, this would query KPIs, monitors, and generate AI summaries
        content = {
            "summary": f"Scheduled insight: {insight.name}",
            "kpis_monitored": insight.included_kpis,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return content

    def _calculate_next_run(self, insight: ScheduledInsight) -> datetime:
        """Calculate the next run time based on the cron schedule."""
        # In production, use a cron parser (e.g., croniter)
        from datetime import timedelta
        return datetime.now(timezone.utc) + timedelta(hours=24)

    async def update_next_run(self, insight: ScheduledInsight):
        """Update the next run time for an insight."""
        insight.next_run_at = self._calculate_next_run(insight)