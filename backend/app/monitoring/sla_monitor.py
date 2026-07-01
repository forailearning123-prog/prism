import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SLAMetric, SLABreachRecord

logger = logging.getLogger(__name__)


class SLAMonitor:
    """Monitors SLA metrics and tracks breaches."""

    async def check_all(self, db: AsyncSession):
        """Check all active SLA metrics for breaches."""
        result = await db.execute(
            select(SLAMetric).where(SLAMetric.is_active == True)
        )
        metrics = result.scalars().all()

        for metric in metrics:
            try:
                await self._check_metric(metric, db)
            except Exception as e:
                logger.error(f"Error checking SLA metric {metric.id}: {e}")

    async def _check_metric(self, metric: SLAMetric, db: AsyncSession):
        """Check a single SLA metric for breach."""
        current_value = await self._get_current_value(metric, db)
        if current_value is None:
            return

        metric.current_value = current_value
        metric.last_measured_at = datetime.now(timezone.utc)

        # Check for breach
        if metric.breach_threshold is not None and current_value > metric.breach_threshold:
            metric.status = "breached"
            metric.breaches += 1

            deviation = current_value - metric.target_value
            breach_record = SLABreachRecord(
                sla_id=metric.id,
                value_at_breach=current_value,
                threshold=metric.target_value,
                deviation=deviation,
            )
            db.add(breach_record)
            logger.warning(f"SLA breach: {metric.name} (value: {current_value}, threshold: {metric.breach_threshold})")
        else:
            metric.status = "compliant"

        # Update trend
        metric.trend = self._calculate_trend(metric, current_value)

        await db.commit()

    def _calculate_trend(self, metric: SLAMetric, current_value: float) -> str:
        """Calculate the trend direction."""
        if metric.current_value is not None:
            if current_value > metric.current_value:
                return "up"
            elif current_value < metric.current_value:
                return "down"
        return "neutral"

    async def _get_current_value(self, metric: SLAMetric, db: AsyncSession) -> Optional[float]:
        """Get the current value for an SLA metric."""
        # In production, query the actual metric source
        return None

    async def measure(self, sla_id: int, value: float, db: AsyncSession) -> SLAMetric:
        """Manually record a measurement for an SLA metric."""
        metric = await db.get(SLAMetric, sla_id)
        if not metric:
            raise ValueError(f"SLA metric {sla_id} not found")

        metric.current_value = value
        metric.last_measured_at = datetime.now(timezone.utc)

        if metric.breach_threshold is not None and value > metric.breach_threshold:
            metric.status = "breached"
            metric.breaches += 1
            breach = SLABreachRecord(
                sla_id=metric.id,
                value_at_breach=value,
                threshold=metric.target_value,
                deviation=value - metric.target_value,
            )
            db.add(breach)
        else:
            metric.status = "compliant"

        metric.trend = self._calculate_trend(metric, value)
        await db.commit()
        await db.refresh(metric)
        return metric